from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import subprocess, time, os, json, threading, cv2, numpy as np
from datetime import datetime
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

CAPTURE_DIR = "/home/nur/captures"
TARGET_DIR = "/home/nur/targets"
EVENT_LOG = "/home/nur/events.json"
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(TARGET_DIR, exist_ok=True)
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
    picam2 = None
    camera_lock = threading.Lock()
except:
    CAMERA_AVAILABLE = False

try:
    from ultralytics import YOLO
    model = YOLO('yolov8n.pt')
    ML_AVAILABLE = True
except:
    ML_AVAILABLE = False
    model = None


autonomous_state = {
    'active': False,
    'mode': None,
    'target_image': None,
    'detections': [],
    'mission_complete': False,
    'thread':  None
}

sensor_data = {
    'depth': 0.0,
    'temperature': 25.0,
    'battery': 100.0,
    'heading': 0.0
}

# ========================================
# PROPER UNDERWATER IMAGE ENHANCEMENT PIPELINE
# Fixed order:  Denoise → Red recovery → CLAHE → Gentle sharpen
# ========================================

def underwater_red_recovery(image):
    """
    Recover red channel lost underwater
    Uses adaptive histogram equalization on red channel only
    """
    try:
        b, g, r = cv2.split(image)
        
        # Adaptive red channel recovery based on depth simulation
        r_avg = np.mean(r)
        g_avg = np.mean(g)
        b_avg = np.mean(b)
        
        # If red is significantly lower than blue/green = underwater effect
        if r_avg < (b_avg * 0.8) or r_avg < (g_avg * 0.8):
            # Apply gentle red boost
            r = cv2.equalizeHist(r)
            # Blend with original to avoid oversaturation
            r = cv2.addWeighted(r, 0.6, cv2.split(image)[2], 0.4, 0)
        
        enhanced = cv2.merge([b, g, r])
        return enhanced
    except: 
        return image

def denoise_preserve_detail(image):
    """
    Denoise first to reduce grain before any enhancement
    Uses bilateral filter - preserves edges while smoothing
    """
    try:
        # Bilateral filter:  smooth but preserve edges
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        return denoised
    except: 
        return image

def apply_clahe_gentle(image):
    """
    Gentle CLAHE - only on luminance, keep colors natural
    Lower clipLimit to avoid noise amplification
    """
    try:
        # Convert to LAB (separate luminance from color)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Gentle CLAHE only on lightness
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Merge back
        enhanced_lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return enhanced
    except:
        return image

def white_balance_gray_world(image):
    """
    Auto white balance using gray world assumption
    Makes colors more natural
    """
    try:
        result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])

        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)

        result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
        return result
    except:
        return image

def sharpen_unsharp_mask(image):
    """
    Gentle sharpening using unsharp mask
    Better than kernel-based sharpening
    """
    try:
        gaussian = cv2.GaussianBlur(image, (5, 5), 1.0)
        sharpened = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
        return sharpened
    except:
        return image



def enhance_for_streaming(image):
    """
    Fast, natural enhancement for live stream: Denoise → WB → Gentle CLAHE → Brightness Boost
    """
    try:
        step1 = denoise_preserve_detail(image)
        step2 = white_balance_gray_world(step1)
        step3 = apply_clahe_gentle(step2)
        hsv = cv2.cvtColor(step3, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, 20)  # 0-255 এর মধ্যে একটু বাড়িয়ে দেখুন
        step4 = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)
        return step4
    except:
        return image


def enhance_for_photo(image):
    """
    Full quality enhancement for saved photos.
    Extra denoising pass, white balance, gentle red recovery, gentle CLAHE, gentle sharpen.
    """
    try:
        # Extra denoising (for saving)
        step1 = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        # White balance
        step2 = white_balance_gray_world(step1)
        # Red recovery (very gentle blending): oversaturate না হয় খেয়াল রাখুন!
        step3 = underwater_red_recovery(step2)  # ফাংশনের ভিতরে blend হালকা দিন (r = cv2.addWeighted(r, 0.4, cv2.split(image)[2], 0.6, 0))
        # Gentle CLAHE
        step4 = apply_clahe_gentle(step3)  # clipLimit যেমন 1.5 বা 2.0
        # Gentle sharpening (কমাতে পারেন, e.g. image=1.2, gaussian=-0.2)
        step5 = sharpen_unsharp_mask(step4)
        return step5
    except:
        return image
# ========================================
# CAMERA INITIALIZATION - PROPER SETTINGS
# ========================================

def init_camera():
    global picam2
    if not CAMERA_AVAILABLE:
        return False
    try:
        if picam2 is None: 
            picam2 = Picamera2()
            
            # OPTIMAL CAMERA SETTINGS
            config = picam2.create_video_configuration(
                main={"size": (1920, 1080), "format": "RGB888"},
                controls={
                    "FrameRate": 30,
                    
                    # Disable auto settings that cause problems
                    "AeEnable": False,           # Manual exposure
                    "AwbEnable": False,          # Manual white balance (we do it in software)
                    
                    # Manual fixed settings
                    "ExposureTime": 30000,       # Fixed exposure
                    "AnalogueGain": 2.0,         # Fixed gain
                    
                    # Disable hardware processing
                    "Brightness": 0.0,           # No hardware brightness
                    "Contrast": 1.0,             # Neutral contrast
                    "Saturation": 1.0,           # Neutral saturation
                    "Sharpness": 0.0,            # No hardware sharpening (we do it better)
                    
                    # Color correction
                    "ColourGains": (1.5, 1.8),   # (Red, Blue) - boost red for underwater
                    
                    # Noise reduction
                    "NoiseReductionMode": 2      # High quality noise reduction
                }
            )
            picam2.configure(config)
            picam2.start()
            time.sleep(2)
            print("✅ Camera initialized - Natural Color Mode")
        return True
    except Exception as e:
        print(f"❌ Camera init failed: {e}")
        return False

def log_event(etype, data):
    try:
        events = json.load(open(EVENT_LOG)) if os.path.exists(EVENT_LOG) else []
        event = {'timestamp': datetime.now().isoformat(), 'type': etype, 'data': data}
        events.append(event)
        json.dump(events[-100:], open(EVENT_LOG, 'w'), indent=2)
        return event
    except: 
        return None

def motor_control(action):
    print(f"🎮 Motor:  {action}")
    log_event('motor', {'action': action})

# ========================================
# MOTOR CONTROL ROUTES
# ========================================

@app.route('/forward', methods=['POST'])
def forward():
    motor_control('forward')
    return jsonify({'status': 'success'})

@app.route('/backward', methods=['POST'])
def backward():
    motor_control('backward')
    return jsonify({'status': 'success'})

@app.route('/left', methods=['POST'])
def left():
    motor_control('left')
    return jsonify({'status': 'success'})

@app.route('/right', methods=['POST'])
def right():
    motor_control('right')
    return jsonify({'status': 'success'})

@app.route('/stop', methods=['POST'])
def stop():
    motor_control('stop')
    return jsonify({'status': 'success'})

@app.route('/surface', methods=['POST'])
def surface():
    print("🌊 SURFACING")
    motor_control('surface')
    log_event('mission', {'action': 'surface'})
    return jsonify({'status': 'success'})

# ========================================
# CAMERA STREAM - NATURAL QUALITY
# ========================================

@app.route('/camera/stream')
def camera_stream():
    def generate():
        init_camera()
        while True:
            try:
                if picam2 is None: 
                    break

                with camera_lock:
                    frame = picam2.capture_array()

                # নিচে চাইলে কম রেজ ও লাইট enhancement রাখতে পারেন:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # স্ট্রিমিং-এ রিসাইজ (bandwidth/performance-এর জন্য):
                stream_bgr = cv2.resize(frame_bgr, (960, 540))
                # চাইলে শুধু হালকা ওয়াইট ব্যালেন্স দিতে পারেন (পারফরমেন্স বাড়ে):
                enhanced_frame = white_balance_gray_world(stream_bgr)

                # YOLO detection (উন্নত না থাকলে skip হবে)
                if autonomous_state['active'] and ML_AVAILABLE:
                    results = model(enhanced_frame, verbose=False)
                    enhanced_frame = results[0].plot()

                frame_rgb = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                buf = io.BytesIO()
                # 75 হলে পারফর্মেন্স ভালো হয়, ন্যাচারাল ব্যালেন্স:
                img.save(buf, format='JPEG', quality=75, optimize=True)

                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.getvalue() + b'\r\n')
                time.sleep(0.01)  # ছোট রাখলে FPS বাড়ে

            except Exception as e:
                print(f"Stream error: {e}")
                break
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/capture', methods=['POST'])
def capture():
    try:
        init_camera()
        filename = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(CAPTURE_DIR, filename)
        
        with camera_lock:
            frame = picam2.capture_array()
        
        # Convert and full enhancement
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        enhanced = enhance_for_photo(frame_bgr)
        
        # Save high quality
        cv2.imwrite(filepath, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        log_event('capture', {'filename': filename})
        return jsonify({'success': True, 'filename': filename})
    except Exception as e: 
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# TARGET UPLOAD
# ========================================

@app. route('/target/upload', methods=['POST'])
def upload_target():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image'}), 400
        
        file = request.files['image']
        filename = f"target_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(TARGET_DIR, filename)
        file.save(filepath)
        
        # Load and enhance
        target_img = cv2.imread(filepath)
        enhanced_target = enhance_for_photo(target_img)
        cv2.imwrite(filepath, enhanced_target, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        autonomous_state['target_image'] = enhanced_target
        log_event('target', {'filename': filename})
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# AUTONOMOUS - YOLO
# ========================================

def autonomous_yolo():
    global autonomous_state
    print("🤖 YOLO Detection Started")
    init_camera()
    
    target_class = autonomous_state. get('target_class', 'person')
    
    while autonomous_state['active'] and not autonomous_state['mission_complete']:
        try:
            if picam2 is None: 
                break
            
            with camera_lock:
                frame = picam2.capture_array()
            
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Clean enhancement for better YOLO accuracy
            enhanced_frame = enhance_for_streaming(frame_bgr)
            
            # YOLO detection
            results = model(enhanced_frame, verbose=False)
            
            for box in results[0].boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls]
                
                # Higher confidence threshold to reduce false positives
                if target_class. lower() in class_name.lower() and conf > 0.7:
                    print(f"🎯 TARGET FOUND: {class_name} ({conf:.2f})")
                    
                    # Save with full enhancement
                    final_frame = enhance_for_photo(frame_bgr)
                    filename = f"found_{class_name}_{datetime. now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    filepath = os.path.join(CAPTURE_DIR, filename)
                    
                    annotated_frame = results[0]. plot()
                    cv2.imwrite(filepath, annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    event = log_event('detection', {
                        'target':  class_name,
                        'confidence': conf,
                        'filename': filename
                    })
                    autonomous_state['detections'].append(event)
                    
                    autonomous_state['mission_complete'] = True
                    motor_control('stop')
                    time.sleep(1)
                    motor_control('surface')
                    
                    log_event('mission', {'status': 'complete', 'target': class_name})
                    print("✅ MISSION COMPLETE!")
                    break
            
            if not autonomous_state['mission_complete']:
                motor_control('forward')
                time.sleep(0.5)
                motor_control('stop')
            
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ Error:  {e}")
            time.sleep(1)
    
    motor_control('stop')

# ========================================
# AUTONOMOUS - TARGET SEARCH
# ========================================

def autonomous_target_search():
    global autonomous_state
    print("🤖 Target Search Started")
    init_camera()
    
    if autonomous_state['target_image'] is None:
        print("❌ No target image")
        return
    
    orb = cv2.ORB_create(nfeatures=2000)
    target_gray = cv2.cvtColor(autonomous_state['target_image'], cv2.COLOR_BGR2GRAY)
    kp_target, des_target = orb. detectAndCompute(target_gray, None)
    
    if des_target is None:
        print("❌ No features")
        return
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    while autonomous_state['active'] and not autonomous_state['mission_complete']: 
        try:
            if picam2 is None:
                break
            
            with camera_lock:
                frame = picam2.capture_array()
            
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            enhanced_frame = enhance_for_streaming(frame_bgr)
            
            gray = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2GRAY)
            kp_frame, des_frame = orb. detectAndCompute(gray, None)
            
            if des_frame is not None:
                matches = bf. match(des_target, des_frame)
                good_matches = [m for m in matches if m. distance < 50]
                
                if len(good_matches) > 25:
                    print(f"🎯 TARGET FOUND!  Matches: {len(good_matches)}")
                    
                    final_frame = enhance_for_photo(frame_bgr)
                    filename = f"target_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    filepath = os.path. join(CAPTURE_DIR, filename)
                    
                    result_img = cv2.drawMatches(
                        autonomous_state['target_image'], kp_target,
                        final_frame, kp_frame,
                        good_matches[: 30], None,
                        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
                    )
                    cv2.imwrite(filepath, result_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    event = log_event('detection', {
                        'target': 'Custom Target',
                        'matches': len(good_matches),
                        'filename': filename
                    })
                    autonomous_state['detections'].append(event)
                    
                    autonomous_state['mission_complete'] = True
                    motor_control('stop')
                    time.sleep(1)
                    motor_control('surface')
                    
                    log_event('mission', {'status': 'complete', 'matches': len(good_matches)})
                    print("✅ MISSION COMPLETE!")
                    break
            
            if not autonomous_state['mission_complete']:
                motor_control('forward')
                time.sleep(0.5)
                motor_control('stop')
            
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
    
    motor_control('stop')

# ========================================
# AUTONOMOUS ROUTES
# ========================================

@app.route('/autonomous/start', methods=['POST'])
def start_autonomous():
    global autonomous_state
    
    if autonomous_state['active']: 
        return jsonify({'success': False, 'error': 'Already running'}), 400
    
    data = request.get_json() or {}
    mode = data.get('mode', 'yolo')
    
    autonomous_state['active'] = True
    autonomous_state['mission_complete'] = False
    autonomous_state['detections'] = []
    autonomous_state['mode'] = mode
    
    if mode == 'yolo': 
        if not ML_AVAILABLE:
            return jsonify({'success': False, 'error': 'ML unavailable'}), 500
        
        target = data.get('target', 'person')
        autonomous_state['target_class'] = target
        thread = threading.Thread(target=autonomous_yolo, daemon=True)
    
    elif mode == 'target': 
        if autonomous_state['target_image'] is None:
            return jsonify({'success': False, 'error':  'Upload target first'}), 400
        thread = threading.Thread(target=autonomous_target_search, daemon=True)
    
    else:
        return jsonify({'success': False, 'error': 'Invalid mode'}), 400
    
    thread.start()
    autonomous_state['thread'] = thread
    
    log_event('autonomous', {'action': 'started', 'mode': mode})
    
    return jsonify({'success': True, 'message': 'Autonomous started', 'mode': mode})

@app.route('/autonomous/stop', methods=['POST'])
def stop_autonomous():
    global autonomous_state
    autonomous_state['active'] = False
    motor_control('stop')
    log_event('autonomous', {'action':  'stopped'})
    return jsonify({'success': True, 'detections': len(autonomous_state['detections'])})

@app.route('/autonomous/status', methods=['GET'])
def autonomous_status():
    return jsonify({
        'success': True,
        'active':  autonomous_state['active'],
        'mode': autonomous_state['mode'],
        'detections': len(autonomous_state['detections']),
        'mission_complete': autonomous_state['mission_complete']
    })

# ========================================
# SENSORS
# ========================================

@app. route('/sensors', methods=['GET'])
def get_sensors():
    sensor_data['depth'] += np.random.uniform(-0.1, 0.1)
    sensor_data['depth'] = max(0, sensor_data['depth'])
    sensor_data['temperature'] = 25 + np.random.uniform(-0.5, 0.5)
    sensor_data['battery'] = max(0, sensor_data['battery'] - 0.01)
    return jsonify({'success': True, 'data': sensor_data})

# ========================================
# EVENTS & PHOTOS
# ========================================

@app.route('/events', methods=['GET'])
def get_events():
    try:
        events = json.load(open(EVENT_LOG)) if os.path.exists(EVENT_LOG) else []
        return jsonify({'success': True, 'events': events[-20:]})
    except:
        return jsonify({'success': True, 'events': []})

@app.route('/captures/<filename>')
def serve_capture(filename):
    try:
        filepath = os.path.join(CAPTURE_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/captures/list', methods=['GET'])
def list_captures():
    try:
        files = []
        if os.path.exists(CAPTURE_DIR):
            for filename in sorted(os.listdir(CAPTURE_DIR), reverse=True):
                if filename. endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(CAPTURE_DIR, filename)
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'timestamp': stat.st_mtime,
                        'url': f'/captures/{filename}'
                    })
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'camera':  CAMERA_AVAILABLE,
        'ml': ML_AVAILABLE,
        'autonomous': autonomous_state['active'],
        'enhancement': 'Natural Underwater Pipeline'
    })

# ========================================
# START SERVER
# ========================================

if __name__ == '__main__': 
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 SUBMARINE BACKEND - NATURAL COLOR")
    print(f"📷 Camera: {'✅' if CAMERA_AVAILABLE else '❌'}")
    print(f"🤖 YOLO: {'✅' if ML_AVAILABLE else '❌'}")
    print("🌊 Enhancement:  Proper Underwater Pipeline")
    print("🎨 Processing Order:  Denoise → WB → Red Recovery → CLAHE → Sharpen")
    print("💡 Camera: Manual Exposure, No Auto Processing")
    print("📸 Result: Natural Colors, Low Noise, Real-life Look")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    init_camera()
    app.run(host='0.0.0.0', port=5000, threaded=True)
