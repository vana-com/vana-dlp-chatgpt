import subprocess

def main():
    subprocess.run(["poetry", "run", "pre-commit", "autoupdate"], check=True)
    subprocess.run(["poetry", "run", "pre-commit", "install"], check=True)
    print("Project setup complete. Pre-commit hooks installed.")

if __name__ == "__main__":
    main()
