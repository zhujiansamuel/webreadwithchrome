####################
  Chrome Extension
####################

1.Prepare chrome extension files `ChromeExtensionForWebread-master`, or download from `https://github.com/zhujiansamuel/ChromeExtensionForWebread.git`;

2.Please make sure `Google Chrome ` is installed on your computer;

3.Copy `chrome://extensions/` and paste it into the address bar, press enter to enter the extension page;

4.After clicking the xx button, select the `ChromeExtensionForWebread-master` folder, and click `Select Folder`;

5.Please check if you can see the plugin named `LyDN note` in the chrome extension.




####################
       WebSite
####################

1.Prepare the project file `webreadwithchrome-master`, or download it from `https://github.com/zhujiansamuel/webreadwithchrome.git.`；

2.Please make sure you have installed python3.8.You can check this by simply running:
`$ python --version`；

3.Open the Start menu and type `cmd`,and then, run the following command to ensure you have pip installed in your system:
`$ pip --version`;

4.Install pipenv by running the following command:
`$ pip install --user pipenv`;

5.Run the following command:
`$ py -m site --user-site`

A sample output can be:

`C:\Users\jetbrains\AppData\Roaming\Python\Python37\site-packages`；

6.Replace site-packages with Scripts in this path to receive a string for adding to the PATH variable, for example:
`$ setx PATH "%PATH%;C:\Users\jetbrains\AppData\Roaming\Python\Python37\Scripts"`；

7.To install packages, change into project’s directory (./webreadwithchrome-master) and run:
`$ pipenv install requests`；

8.Change into the project’s directory(./webreadwithchrome-master), and run the following commands:
`$ python manage.py runserver`

9.Now that the server’s running, visit `http://127.0.0.1:8000/` with your Web browser.


####################
       Notice
####################

If you have any questions, you can contact:

samuelsyuken@gmail.com




####################
     Thank you!
####################
