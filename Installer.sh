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

git clone --no-hardlinks ~/PycharmProjects/SignInProgram/SignInProgram/.git/  # TODO Replace with URL to git release branch

pip install -Ur SignInProgram/requirements.txt pip

echo Install Complete!
