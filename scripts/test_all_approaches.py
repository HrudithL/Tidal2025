"""
Test all 4 optimization approaches and determine which works
"""
import os
import json
import subprocess
from pathlib import Path

def create_and_test_approaches():
    """Create model packages for all 4 approaches and test them"""
    
    approaches = {
        "cpu_minimal": {
            "inference": "inference_cpu_minimal.py",
            "instance": "ml.m5.large",
            "description": "CPU-only minimal (no AI models)"
        },
        "lazy_loading": {
            "inference": "inference_lazy.py", 
            "instance": "ml.m5.xlarge",
            "description": "Lazy loading (models load on demand)"
        },
        "small_models": {
            "inference": "inference_small.py",
            "instance": "ml.m5.xlarge",
            "description": "Smallest AI models (tiny Whisper)"
        },
        "cpu_large": {
            "inference": "inference_cpu_large.py",
            "instance": "ml.m5.2xlarge",
            "description": "CPU-only for large instances"
        }
    }
    
    results = {}
    
    print("=" * 60)
    print("Testing All SageMaker Optimization Approaches")
    print("=" * 60)
    
    for approach_name, config in approaches.items():
        print(f"\nTesting: {config['description']}")
        print(f"Instance: {config['instance']}")
        print("-" * 40)
        
        # Create model package for this approach
        package_name = f"sonicmuse-{approach_name}.tar.gz"
        
        try:
            # Copy approach-specific inference.py
            inference_src = f"sagemaker/model/{config['inference']}"
            inference_dst = "sagemaker/model/inference.py"
            
            if os.path.exists(inference_src):
                # Create model package
                subprocess.run([
                    "tar", "czf", package_name,
                    "-C", "sagemaker/model",
                    "inference.py"
                ], check=True)
                
                print(f"[OK] Created package: {package_name}")
                
                # Upload to S3
                result = upload_and_deploy(approach_name, config['instance'], package_name)
                results[approach_name] = result
                
            else:
                print(f"[ERROR] Inference file not found: {inference_src}")
                results[approach_name] = {"status": "file_not_found"}
                
        except Exception as e:
            print(f"[ERROR] {approach_name} failed: {e}")
            results[approach_name] = {"status": "error", "message": str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results.items():
        status = result.get("status", "unknown")
        desc = approaches[name]["description"]
        print(f"\n{name}: {desc}")
        print(f"  Status: {status}")
        if "endpoint_url" in result:
            print(f"  Endpoint: {result['endpoint_url']}")
    
    # Determine best approach
    successful = [name for name, r in results.items() if r.get("status") == "deployed"]
    
    if successful:
        print(f"\n[SUCCESS] Working approaches: {', '.join(successful)}")
        print(f"\n[RECOMMENDED] Best approach: {successful[0]}")
    else:
        print("\n[WARNING] No approaches successfully deployed")
    
    return results

def upload_and_deploy(approach_name, instance_type, package_file):
    """Upload and deploy a specific approach"""
    
    # This is a simplified version - in practice, you'd use boto3
    print(f"[INFO] Would deploy {approach_name} to {instance_type}")
    
    return {
        "status": "pending_deployment",
        "approach": approach_name,
        "instance": instance_type
    }

if __name__ == "__main__":
    results = create_and_test_approaches()
    
    # Save results
    with open("sagemaker_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n[OK] Test results saved to sagemaker_test_results.json")
