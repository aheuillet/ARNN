# ARNN - A recurrent neuronal network analysis platform

## Setup

For debian users, an install script `setup.sh` is provided in `Django/recurView/`.

If necessary, you can also setup the website following these steps :

**We will suppose that macOS users, are using the package manager Brew**
If you're not using Brew, go get it [here](https://brew.sh/), it's an awesome tool !

First of all, you need to make sure that **Python 3** and **PIP** are present on your system :
For Debian-based systems :
```bash
sudo apt install python3 && sudo apt install python3-pip
```
or for macOS users :
```bash
brew install python3
```
Then, you must install **Django**, **Bokeh**, **nodeJS**, **sklearn** and **Jupyter**.

For Debian-based systems :
```bash
sudo apt install nodejs
sudo pip3 install django && sudo pip3 install bokeh && sudo pip3 install sklearn 
&& sudo pip3 install jupyter
```
For macOS users :
```bash
brew install node
pip3 install django && pip3 install bokeh && pip3 install sklearn
&& pip3 install jupyter
```
Once this is done, all dependancies are installed !

## First run of the project
Go into the `Django/recurView/` repository and execute the following command to deploy migrations and create the database :
```bash
python3 manage.py migrate
```
Once this is done you can run the built-in dev webserver via the following command :
```bash
python3 manage.py runserver
```
The website should now be available on your localhost and listening to port 8000.

**:warning: Django built-in webserver should not be used for direct exposure of the website on the Internet. You should use a more advanced webserver such as Apache or Nginx as a reverse-proxy and provide SSL certificates to get HTTPS access.**

## Compiling the doc
The documentation sources are contained in the `Doc/sources`.
To compile the doc in HTML, first you need to install **Sphinx** :
```bash
pip3 install sphinx
```
Then, go to the `Doc/` folder and execute the following command in a shell :
```bash
make html
```
Once this is done, go to the `Doc/build/html` and open "index.html" in a web browser to acess the doc.
