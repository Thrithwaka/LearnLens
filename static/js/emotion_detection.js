
/**
 * EmotionDetection class for detecting facial expressions using DeepFace
 */
class EmotionDetection {
    constructor() {
      this.model = null;
      this.isModelLoaded = false;
      this.lastEmotions = null;
      this.emotionUpdateInterval = 500; // Update interval in ms
      this.lastUpdateTime = 0;
    }
  
    /**
     * Initialize the emotion detection model
     */
    async init() {
      try {
        // Load the model using fetch
        const response = await fetch('/api/load_emotion_model');
        if (!response.ok) {
          throw new Error('Failed to load emotion model');
        }
        
        console.log('Emotion detection model initialized');
        this.isModelLoaded = true;
        return true;
      } catch (error) {
        console.error('Error initializing emotion detection:', error);
        return false;
      }
    }
  
    /**
     * Detect emotions from canvas/video element
     * This will make an API call to the backend for processing
     * @param {HTMLCanvasElement} canvas - Canvas element containing the face image
     * @returns {Object} - Detected emotions with confidence values
     */
    async detectEmotions(canvas) {
      if (!this.isModelLoaded) {
        console.error('Emotion model not loaded');
        return null;
      }
  
      // Limit update frequency
      const now = Date.now();
      if (now - this.lastUpdateTime < this.emotionUpdateInterval) {
        return this.lastEmotions;
      }
  
      try {
        // Convert canvas to data URL
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Send to server for processing
        const response = await fetch('/api/detect_emotions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ image_data: imageData })
        });
  
        if (!response.ok) {
          throw new Error('Failed to detect emotions');
        }
  
        const result = await response.json();
        this.lastEmotions = result.emotions;
        this.lastUpdateTime = now;
        
        return this.lastEmotions;
      } catch (error) {
        console.error('Error detecting emotions:', error);
        return this.lastEmotions; // Return last known emotions on error
      }
    }
  }
  </lov-write>
  
  