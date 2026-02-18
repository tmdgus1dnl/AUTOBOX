
import os
import json
import base64

def decode_images():
    # Define directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    img_dir = os.path.join(data_dir, 'img')

    # Ensure destination directory exists
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
        print(f"Created directory: {img_dir}")

    # Process files
    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return

    files_processed = 0
    for filename in os.listdir(data_dir):
        if filename.startswith('box_img_') and filename.endswith('.json'):
            json_path = os.path.join(data_dir, filename)
            
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                if 'dest' in data:
                    base64_data = data['dest']
                    # Remove prefix if present (e.g., "data:image/jpeg;base64,")
                    if ',' in base64_data:
                        base64_data = base64_data.split(',')[1]
                    
                    try:
                        image_data = base64.b64decode(base64_data)
                        
                        # Create image filename (replace .json with .jpg)
                        img_filename = filename.replace('.json', '.jpg')
                        img_path = os.path.join(img_dir, img_filename)
                        
                        with open(img_path, 'wb') as img_file:
                            img_file.write(image_data)
                        
                        print(f"Saved: {img_path}")
                        files_processed += 1
                    except Exception as e:
                        print(f"Error decoding/saving {filename}: {e}")
                else:
                    print(f"Skipping {filename}: No 'dest' field found")
            
            except json.JSONDecodeError:
                print(f"Error reading JSON from {filename}")
            except Exception as e:
                print(f"Unexpected error processing {filename}: {e}")

    print(f"Finished processing. Total images saved: {files_processed}")

if __name__ == "__main__":
    decode_images()
