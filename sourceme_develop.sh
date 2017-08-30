# GOOD: source develop.sh
# BAD: ./develop.sh
# BAD: sh develop.sh

if [ ! -e env/ ]; then
    virtualenv env
fi

source env/bin/activate
pip install -r requirements.txt
python setup.py develop --uninstall
python setup.py develop
