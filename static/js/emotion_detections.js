
/**
 * Emotion Detection for LearnLens Quiz System
 * Handles real-time facial emotion analysis during quizzes
 */

class EmotionDetection {
    constructor() {
      this.isActive = false;
      this.captureInterval = null;
      this.emotionData = {
        happy: 0,
        neutral: 0.5,
        sad: 0,
        angry: 0,
        fear: 0,
        disgust: 0,
        surprise: 0
      };
      this.lastCapture = 0;
      this.captureFrequency = 2000; // Capture every 2 seconds to reduce server load
      this.onEmotionUpdate = null; // Callback function for emotion updates
    }
  
    async init() {
      try {
        // Check if camera is available
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        
        if (videoDevices.length === 0) {
          console.error('No camera detected');
          return false;
        }
        
        return true;
      } catch (error) {
        console.error('Error initializing camera:', error);
        return false;
      }
    }
  
    start(videoElement, onEmotionUpdate = null) {
      if (this.isActive) return;
      
      this.isActive = true;
      this.onEmotionUpdate = onEmotionUpdate;
      const canvas = document.getElementById('canvas');
      
      // Start capturing and analyzing emotions
      this.captureInterval = setInterval(() => {
        const now = Date.now();
        
        // Only capture at the specified frequency
        if (now - this.lastCapture >= this.captureFrequency) {
          this.lastCapture = now;
          this.captureAndAnalyze(videoElement, canvas);
        }
      }, 100);
    }
  
    stop() {
      this.isActive = false;
      if (this.captureInterval) {
        clearInterval(this.captureInterval);
        this.captureInterval = null;
      }
    }
  
    captureAndAnalyze(videoElement, canvas) {
      if (!this.isActive || !videoElement.videoWidth) return;
      
      const ctx = canvas.getContext('2d');
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;
      
      // Draw the current video frame to the canvas
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
      
      // Convert canvas to base64 image
      const imageData = canvas.toDataURL('image/jpeg', 0.7);
      
      // Send to server for emotion analysis
      fetch('/analyze_emotion', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image_data: imageData })
      })
      .then(response => response.json())
      .then(result => {
        if (result.success) {
          this.emotionData = result.emotions;
          this.updateEmotionDisplay(result.satisfaction_levels);
          
          // Call the callback function if provided
          if (this.onEmotionUpdate) {
            this.onEmotionUpdate(result.satisfaction_levels);
          }
        }
      })
      .catch(error => {
        console.error('Error analyzing emotions:', error);
      });
    }
  
    updateEmotionDisplay(satisfaction_levels) {
      // Update the UI with satisfaction levels
      this.updateEmotionBar('happy', satisfaction_levels.satisfied);
      this.updateEmotionBar('neutral', satisfaction_levels.neutral);
      this.updateEmotionBar('unsatisfied', satisfaction_levels.unsatisfied);
    }
  
    updateEmotionBar(emotion, value) {
      const bar = document.getElementById(`${emotion}-bar`);
      const valueElement = document.getElementById(`${emotion}-value`);
      
      if (bar && valueElement) {
        const percentage = Math.round(value * 100);
        bar.style.width = `${percentage}%`;
        valueElement.textContent = `${percentage}%`;
      }
    }
  
    getEmotions() {
      return this.emotionData;
    }
  }
  
  // Make available globally
  window.EmotionDetection = EmotionDetection;
  