echo Starting install of the Sign In Program.
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3"
    exit
fi

if ! command -v pip3 &> /dev/null
then
    echo "pip3 is not installed. Please install pip3"
    exit
fi

git clone -b release --single-branch https://github.com/LinuxMaster393/SignInProgram.git

pip install -Ur SignInProgram/requirements.txt pip

cat > ~/.local/share/applications/SignInProgram.desktop << EOF1
[Desktop Entry]
Name=Sign In Program
Comment=A system for keeping record of who attends an event, for how long, and upload those records to a Google Sheet
Exec=bash -c 'cd $PWD/SignInProgram && python3 $PWD/SignInProgram/main.py %U'
Icon=$PWD/SignInProgram/Icon/icon.png
Terminal=true
Type=Application
EOF1

cat > SignInProgram/SignInProgram.desktop << EOF2
[Desktop Entry]
Name=Sign In Program
Comment=A system for keeping record of who attends an event, for how long, and upload those records to a Google Sheet
Exec=bash -c 'cd $PWD/SignInProgram && python3 $PWD/SignInProgram/main.py %U'
Icon=$PWD/SignInProgram/Icon/icon.png
Terminal=true
Type=Application
EOF2

chmod +x ~/.local/share/applications/SignInProgram.desktop
chmod +x SignInProgram/SignInProgram.desktop

echo Install Complete!
