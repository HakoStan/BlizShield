# BlizShield
TBD :: Description

## Requirements
1. python3.9
2. execute `pip install -r requirements.txt`
3. install NMAP executable and make sure its in your $PATH environment variable

# Wordpress Scanner Plugin
1. We use WPScan that needs to be installed on your computer.
2. To install it - you need to run `gem install wpscan`
NOTE :: `gem` is a part of Ruby. So you'll need ruby installed before.
3. Site to attack details:
```
http://138.68.90.29/
pass: Sup3rSecretPassword
WPScan API KEY - fH62Oxk9nhwtADF9fiEaoSaaIJi1hcEbG2688C2dctk
```
4. On windows you'll also need libcurl.dll
5. put in the env variable the API KEY and name it BLIZSHIELD_WORDPRESS_PLUGIN_API_KEY