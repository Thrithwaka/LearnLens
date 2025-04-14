/**
 * DeepFace Emotion Detection for LearnLens Quiz System
 * Handles real-time facial emotion analysis during quizzes
 */

// Global variables for emotion detection
let emotionDetectionActive = false;
let videoStream = null;
let captureInterval = null;
let lastCaptureTime = 0;
let processingRequest = false;
let errorCount = 0;
let captureFrequency = 1500; // Capture every 1.5 seconds by default
let faceDetected = false;

// Emotion data storage
let emotionData = {
    // Raw emotions from DeepFace
    happy: 0,
    sad: 0,
    angry: 0,
    fear: 0,
    surprise: 0,
    disgust: 0,
    neutral: 0,
    
    // Mapped satisfaction levels
    satisfied: 0,
    unsatisfied: 0
};

/**
 * Initialize emotion detection with webcam
 * @param {HTMLVideoElement} videoElement - Video element for webcam display
 * @param {HTMLElement} statusElement - Element to display camera status
 * @param {HTMLElement} toggleButton - Button to toggle camera on/off
 */
function initializeEmotionDetection(videoElement, statusElement, toggleButton) {
    // Don't initialize if already active
    if (emotionDetectionActive) return;
    
    console.log("Initializing emotion detection...");
    
    // Check for webcam support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError(statusElement, "Your browser doesn't support webcam access");
        return;
    }
    
    // Request camera access
    navigator.mediaDevices.getUserMedia({
        video: {
            width: { ideal: 320 },
            height: { ideal: 240 },
            facingMode: "user"
        }
    })
    .then(function(stream) {
        // Store stream for later cleanup
        videoStream = stream;
        
        // Connect stream to video element
        videoElement.srcObject = stream;
        
        // Update UI
        statusElement.textContent = 'Camera Active';
        statusElement.classList.remove('inactive');
        statusElement.classList.add('active');
        toggleButton.innerHTML = '<i class="fas fa-video-slash"></i> Disable Camera';
        
        // Reset error count
        errorCount = 0;
        
        // Start emotion detection
        startEmotionCapture(videoElement);
        
        // Mark as active
        emotionDetectionActive = true;
        
        console.log("Emotion detection activated successfully");
    })
    .catch(function(error) {
        console.error('Error accessing webcam:', error);
        showError(statusElement, 'Camera access denied');
    });
}

/**
 * Show error message in status element
 * @param {HTMLElement} statusElement - Element to display status
 * @param {string} message - Error message to display
 */
function showError(statusElement, message) {
    statusElement.textContent = message;
    statusElement.classList.remove('active');
    statusElement.classList.add('inactive');
    console.error(message);
}

/**
 * Start capturing frames for emotion analysis
 * @param {HTMLVideoElement} videoElement - Video element with webcam stream
 */
function startEmotionCapture(videoElement) {
    const canvas = document.getElementById('canvas');
    if (!canvas) {
        console.error('Canvas element not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Define capture interval (check more frequently than we capture)
    captureInterval = setInterval(() => {
        const now = Date.now();
        
        // Only capture at the specified frequency and if not currently processing
        if (now - lastCaptureTime >= captureFrequency && !processingRequest) {
            lastCaptureTime = now;
            
            // Mark as processing
            processingRequest = true;
            
            // Ensure video is ready
            if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                // Draw current frame to canvas
                canvas.width = videoElement.videoWidth;
                canvas.height = videoElement.videoHeight;
                ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                
                // Convert to data URL with reduced quality for faster transmission
                const imageData = canvas.toDataURL('image/jpeg', 0.6);
                
                // Send for analysis
                analyzeEmotion(imageData);
            } else {
                processingRequest = false;
            }
        }
    }, 200); // Check more frequently than capture frequency
}

/**
 * Stop emotion detection and clean up resources
 */
function stopEmotionDetection() {
    // Stop capture interval
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
    
    // Stop video stream
    if (videoStream) {
        videoStream.getTracks().forEach(track => {
            track.stop();
        });
        videoStream = null;
    }
    
    // Reset flags
    emotionDetectionActive = false;
    processingRequest = false;
    faceDetected = false;
    
    console.log("Emotion detection stopped");
}

/**
 * Send image data to server for emotion analysis
 * @param {string} imageData - Base64 encoded image data
 */
function analyzeEmotion(imageData) {
    // Create AbortController with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    // Send to server
    fetch('/analyze_emotion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image_data: imageData
        }),
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reset error count on success
            errorCount = 0;
            
            // Update face detection status
            faceDetected = data.face_detected;
            
            // Update face preview if face detected
            if (faceDetected && data.face_image) {
                updateFacePreview(data.face_image);
            } else {
                showNoFaceDetected();
            }
            
            // Update emotion data
            if (data.emotions) {
                updateEmotionDisplay(data.emotions, data.satisfaction_levels);
            }
            
            console.log("Emotion data updated:", data.emotions);
        } else {
            console.warn(data.message || 'Unknown error from server');
            if (!faceDetected) {
                showNoFaceDetected();
            }
        }
    })
    .catch(error => {
        console.error('Error in emotion analysis:', error);
        errorCount++;
        
        // If multiple consecutive errors, slow down capture rate
        if (errorCount > 3) {
            captureFrequency = Math.min(captureFrequency * 1.5, 5000); // Max 5 seconds
            console.log(`Reducing capture frequency to ${captureFrequency}ms due to errors`);
        }
        
        if (!faceDetected) {
            showNoFaceDetected();
        }
    })
    .finally(() => {
        // Mark as done processing
        processingRequest = false;
    });
}

/**
 * Show message when no face is detected
 */
function showNoFaceDetected() {
    const facePreview = document.querySelector('.face-preview');
    if (facePreview) {
        facePreview.innerHTML = `<div class="no-face-detected">No face detected</div>`;
    }
}

/**
 * Update face preview with detected face image
 * @param {string} faceImageData - Base64 encoded face image
 */
function updateFacePreview(faceImageData) {
    const facePreview = document.querySelector('.face-preview');
    if (facePreview) {
        facePreview.innerHTML = `<img src="${faceImageData}" alt="Detected Face" class="face-image">`;
    }
}

/**
 * Update UI with emotion data
 * @param {Object} emotions - Raw emotion data
 * @param {Object} satisfactionLevels - Mapped satisfaction levels
 */
function updateEmotionDisplay(emotions, satisfactionLevels) {
    // Update raw emotion data
    for (const [emotion, value] of Object.entries(emotions)) {
        emotionData[emotion] = value;
        
        // Update UI for detailed emotions if they exist
        updateEmotionBar(emotion, value);
    }
    
    // Update satisfaction levels
    if (satisfactionLevels) {
        for (const [level, value] of Object.entries(satisfactionLevels)) {
            emotionData[level] = value;
            
            // Update UI for satisfaction levels
            updateEmotionBar(level, value);
        }
    }
}

/**
 * Update single emotion bar in UI
 * @param {string} emotion - Emotion name
 * @param {number} value - Emotion value (0-1)
 */
function updateEmotionBar(emotion, value) {
    const bar = document.getElementById(`${emotion}-bar`);
    const valueEl = document.getElementById(`${emotion}-value`);
    
    if (bar && valueEl) {
        const percentage = Math.round(value * 100);
        bar.style.width = `${percentage}%`;
        valueEl.textContent = `${percentage}%`;
        
        // Add visual transition for smoother updates
        if (!bar.style.transition) {
            bar.style.transition = 'width 0.3s ease-in-out';
        }
    }
}

/**
 * Get current emotion data for submission
 * @returns {Object} Current emotion data
 */
function getCurrentEmotionData() {
    return {
        // Face detection status
        face_detected: faceDetected,
        
        // Raw emotions
        happy: emotionData.happy,
        sad: emotionData.sad,
        angry: emotionData.angry,
        fear: emotionData.fear,
        surprise: emotionData.surprise,
        disgust: emotionData.disgust,
        neutral: emotionData.neutral,
        
        // Mapped satisfaction levels
        satisfied: emotionData.satisfied || emotionData.happy, // Fallback to happy if not set
        neutral: emotionData.neutral,
        unsatisfied: emotionData.unsatisfied || 
            (emotionData.sad + emotionData.angry + emotionData.fear + emotionData.disgust) / 4 // Fallback calculation
    };
}