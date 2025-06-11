#!/usr/bin/env python3
"""
检查和升级依赖脚本
"""
import sys
import pkg_resources
import subprocess

def check_package_version(package_name):
    """检查包版本"""
    try:
        version = pkg_resources.get_distribution(package_name).version
        return version
    except pkg_resources.DistributionNotFound:
        return None

def main():
    """检查关键依赖版本"""
    print("🔍 依赖版本检查")
    print("=" * 40)
    
    # 关键依赖
    critical_deps = {
        'websockets': '12.0',
        'httpx': '0.25.0',
        'ormsgpack': '1.4.0',
        'fastapi': '0.104.1',
        'uvicorn': '0.24.0'
    }
    
    needs_upgrade = []
    
    for package, required_version in critical_deps.items():
        current_version = check_package_version(package)
        if current_version:
            print(f"📦 {package}: {current_version} (要求: {required_version})")
            
            # 简单版本比较（不完美但足够用）
            if current_version < required_version:
                needs_upgrade.append(package)
                print(f"   ⚠️ 需要升级")
            else:
                print(f"   ✅ 版本满足要求")
        else:
            print(f"❌ {package}: 未安装")
            needs_upgrade.append(package)
    
    print("\n" + "=" * 40)
    
    if needs_upgrade:
        print(f"⚠️ 需要升级的包: {', '.join(needs_upgrade)}")
        print("\n🔧 升级命令:")
        print("pip install -r requirements.txt --upgrade")
        print("\n或者单独升级关键包:")
        for package in needs_upgrade:
            if package in critical_deps:
                print(f"pip install {package}>={critical_deps[package]} --upgrade")
    else:
        print("✅ 所有依赖版本都满足要求")
    
    # 检查Python版本
    print(f"\n🐍 Python版本: {sys.version}")
    if sys.version_info < (3, 8):
        print("⚠️ 建议使用Python 3.8+以获得更好的兼容性")
    else:
        print("✅ Python版本满足要求")

if __name__ == "__main__":
    main() 