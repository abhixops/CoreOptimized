#!/usr/bin/env python3
"""
Clean CurseForge modpack exports: remove bundled mods that exist on CurseForge
and update manifest.json with proper references.
"""

import json
import os
import shutil
from pathlib import Path
import requests
import zipfile
import sys

class CurseForgePackCleaner:
    def __init__(self, zip_path, output_dir="."):
        self.zip_path = Path(zip_path)
        self.output_dir = Path(output_dir)
        self.cf_api = "https://api.curseforge.com/v1/mods/files"
        self.temp_dir = Path("temp_pack_extract")
        
    def extract_pack(self):
        """Extract modpack ZIP"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir()
        
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        
        print(f"✓ Extracted to {self.temp_dir}")
        
    def find_mod_on_curseforge(self, jar_name):
        """
        Attempt to find a mod on CurseForge by filename (basic approach)
        For production, you'd query the CurseForge API with the mod hash
        """
        # This is a placeholder - in reality you'd use:
        # 1. File hash lookup via CurseForge API
        # 2. Manual lookup by mod name
        
        print(f"⚠ Manual lookup needed for: {jar_name}")
        return None
        
    def get_bundled_mods(self):
        """List all mods in overrides/mods"""
        mods_dir = self.temp_dir / "overrides" / "mods"
        
        if not mods_dir.exists():
            return []
        
        return list(mods_dir.glob("*.jar"))
        
    def load_manifest(self):
        """Load manifest.json"""
        manifest_path = self.temp_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError("manifest.json not found in pack")
        
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def save_manifest(self, manifest):
        """Save updated manifest.json"""
        manifest_path = self.temp_dir / "manifest.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("✓ Updated manifest.json")
    
    def create_cleaned_zip(self):
        """Create cleaned ZIP file"""
        output_zip = self.output_dir / f"{self.zip_path.stem}-cleaned.zip"
        
        # Create new zip with only necessary files
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.temp_dir)
                    
                    # Skip bundled mods (they should be in manifest)
                    if "overrides/mods" in str(arcname):
                        continue
                    
                    zipf.write(file_path, arcname)
        
        print(f"✓ Created cleaned pack: {output_zip}")
        return output_zip
    
    def run_interactive(self):
        """Run interactive cleanup"""
        self.extract_pack()
        
        bundled_mods = self.get_bundled_mods()
        manifest = self.load_manifest()
        
        print(f"\n📦 Found {len(bundled_mods)} mods in overrides/mods:")
        
        mods_to_remove = []
        
        for i, mod_path in enumerate(bundled_mods, 1):
            mod_name = mod_path.name
            print(f"\n{i}. {mod_name}")
            print("   Is this mod available on CurseForge? (y/n/skip)")
            print("   [y] Yes - remove from overrides, add to manifest")
            print("   [n] No - keep in overrides (third-party mod)")
            print("   [s] Skip for now")
            
            choice = input("   > ").strip().lower()
            
            if choice == 'y':
                project_id = input("   Enter CurseForge Project ID: ").strip()
                file_id = input("   Enter CurseForge File ID: ").strip()
                
                # Add to manifest
                if "files" not in manifest:
                    manifest["files"] = []
                
                manifest["files"].append({
                    "projectID": int(project_id),
                    "fileID": int(file_id),
                    "required": True
                })
                
                mods_to_remove.append(mod_path)
                print(f"   ✓ Added to manifest")
            
            elif choice == 'n':
                print(f"   ✓ Will keep in overrides (must be third-party approved)")
        
        # Remove mods from overrides
        for mod_path in mods_to_remove:
            mod_path.unlink()
            print(f"✓ Removed {mod_path.name}")
        
        self.save_manifest(manifest)
        cleaned_zip = self.create_cleaned_zip()
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
        
        print(f"\n✅ Done! Upload this file to CurseForge: {cleaned_zip}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_curseforge_pack.py <modpack.zip>")
        sys.exit(1)
    
    zip_file = sys.argv[1]
    cleaner = CurseForgePackCleaner(zip_file)
    cleaner.run_interactive()