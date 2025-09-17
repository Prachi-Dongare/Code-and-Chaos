from PIL import Image
import os
import numpy as np

def predict_image(image_path):
    # This is a simple, rule-based classifier for the hackathon demo.
    # It checks the average color to make a "prediction."
    try:
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img)
        
        # Calculate the average RGB values
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # Simple rule-based logic
        # If the average color has a high green value, it's a "healthy" plant.
        if avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2] and avg_color[1] > 100:
            prediction = "Healthy Plant"
            confidence = 0.95
            solution = "Your plant appears to be healthy! Keep up the good work."
        # If it's more yellow or brown, it might have a problem.
        elif avg_color[0] > avg_color[1] and avg_color[0] > 100:
            prediction = "Nutrient Deficiency"
            confidence = 0.80
            solution = "Yellowing leaves can indicate a lack of nitrogen. Consider applying a balanced fertilizer."
        else:
            prediction = "Unknown Issue"
            confidence = 0.50
            solution = "The system cannot identify the issue. Please consult an expert for a definitive diagnosis."

        return {
            "prediction": prediction,
            "confidence": confidence,
            "solution": solution
        }
    
    except Exception as e:
        return {
            "prediction": "Error",
            "confidence": 0.0,
            "solution": f"An error occurred: {e}"
        }