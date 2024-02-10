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

echo Checking for updates
git pull https://github.com/LinuxMaster393/SignInProgram.git
pip install -Ur requirements.txt pip
echo Updates complete!