# us-embassy-bot
A repository aiming to help people find an earlier appointment at the US embassy.
It provides the user with the earliest appointment by notifying him with emails.


## 1. Installation 

We use a webdriver for Firefox `geckodriver` which will be controlled by using `selenium`.
To install you should proceed as following. 

### Max OS

With `brew` it is quite straightforward by running:
```
brew install geckodriver
pip3 install -r requirements.txt
```

### Linux (Debian)

On linux you need to download the latest release in a `.tar.gz` format:
```
apt-get install iceweasel
wget https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
sudo sh -c 'tar -x geckodriver -zf geckodriver-v0.26.0-linux64.tar.gz -O > /usr/bin/geckodriver'
sudo chmod +x /usr/bin/geckodriver
rm geckodriver-v0.26.0-linux64.tar.gz
pip3 install -r requirements.txt
```

## 2. Configuration

The `config.json` file should be filled out like this:

```{json}
{
  "webdriver": {
    "headless": true
  },
  "msg_lang": "fr_FR",
  "embassy": {
    "username": "john.doe@gmail.com",
    "password": "mySuperPassword",
    "appointment_number": "00000000"
  },
  "email_notification": {
    "sender": {
      "username": "visa.bot.usa@gmail.com",
      "password": "password",
      "name": "Visa Bot USA"
    },
    "recipient": "john.doe@gmail.com"
  }
}
```

## 3. Run script

```
python3 visa_bot.py
```