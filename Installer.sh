#
# SignInProgram - Record attendance logs and upload to a Google Sheet.
# Copyright (C) 2024 LinuxMaster393
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

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
