"""
Update .env file with unique bucket name
"""
import os
import random
import string

def update_bucket_name():
    """Update .env file with a unique bucket name"""
    
    # Generate unique bucket name
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    unique_bucket = f"sonicmuse-models-{random_suffix}"
    
    print(f"Generated unique bucket name: {unique_bucket}")
    
    # Read current .env file
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update the bucket name line
    new_lines = []
    for line in lines:
        if line.startswith('SAGEMAKER_BUCKET_NAME='):
            new_lines.append(f'SAGEMAKER_BUCKET_NAME={unique_bucket}\n')
        else:
            new_lines.append(line)
    
    # Write updated .env file
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"[OK] Updated .env file with unique bucket name: {unique_bucket}")

if __name__ == "__main__":
    update_bucket_name()
