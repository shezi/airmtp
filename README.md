# airmtp -- Wireless download from your MTP-enabled devices

**Please note**: This is a copy of the repository for a project called "Airnef" originally found on [testcams.com](https://testcams.com/airnef/). I am not the original maintainer, and as such I cannot offer much advice on this code, the protocols or the project.

# original readme

Airmtp is a command line application to do MTP transfers from Canon, Nikon, Sony and other cameras to your computer.

There is also a GUI frontend that can be used to drive the command line application, but the GUI may not contain all options available from the command line.

## Camera Support Feature Matrix

This is a partial list of cameras that were tested. Even if your camera is not listed it may still work. Please notify us if you find a camera that works with airmtp!

| Camera | Select Images in Camera | Select Images on Computer | Realtime Download<sup>1</sup> |
| --- | --- | --- | --- |
| All Nikon cameras with built-in WiFi | Yes | Yes | All DSLRs<sup>2</sup> |
| All Nikon cameras with WU-1a/WU-1b Adapter | No<sup>3</sup> | Yes | Yes |
| All Canon Cameras with WiFi | No | Yes | Yes |
| All Sony Cameras with WiFi  | No | Yes | Staged Realtime<sup>4</sup> |
| Nikon D750, D7200 | Yes | Yes | Yes |
| Nikon J4, J5 | Yes | Yes | Staged Realtime<sup>4</sup> |
| Canon 6D | Yes | Yes | Yes |


<sup>1</sup>An easy way to tell if your camera supports Realtime Download is if it allows you to take photographs while its WiFi interface is enabled and in the mode required by Airmtp. For example most Nikon DSLRs support shooting with WiFi enabled. In contrast, Sony cameras (in the "Send to Computer" mode) and the Nikon J4/J5 require you to leave the WiFi mode before you can use the functionality of the camera again  
<sup>2</sup>Nikon 1 cameras with built-in WiFi such as the J4 and J5 do not support Realtime download but can use staged realtime transfers  
<sup>3</sup>Nikon bodies using an external WU-1a or WU-1b WiFi adapter have no separate menu option for selecting images to upload and the alternate mechanism of selecting images for upload in the playback menu (present in cameras with native WiFi support like the D7200) is unavailable because the playback menu is disabled when WiFi is on for cameras with an external WiFi adapter.  
<sup>4</sup>Staged Realtime means the camera doesn't support taking photographs while in the WiFi mode required by Airmtp but you can achieve faux-realtime transfers by shooting any number of photos in non-WiFi mode then turning your camera's WiFi on to automatically transfer those images to Airmtp, then turn your camera's WiFi back off to resume shooting. You can repeat this any number of times while running a single Airmtp session (no intervention required on computer).


## major features

 * One-button click to download all new images and video from the camera, selected on either the camera or computer by criteria
 * Fast downloads - Airmtp uses optimized Media Transfer Protocol (MTP) parameters for sustained throughput around 2.5 MB/s
 * Realtime download mode - images are transferred to your computer as you shoot them. For cameras without realtime WiFi shooting support an optional staged-realtime process can be used as well.
 * Extensive criteria selection makes it easy to quickly choose which images to download, including by file type (NEF, JPG, MOV, etc...), starting and/or ending capture date, specific camera folders, and media card slot - in any combination. And Airmtp will automatically skip over files you've already downloaded!
 * Renaming engine allows you to customize the names of directories and files for images you download
 * Download exec feature lets you launch your favorite image viewing or editing application for each file downloaded
 * Advanced local caching of MTP metadata allows for very fast click-to-download start times
 * Lets you decide the order that files are downloaded, either oldest first or newest first. That way you can start working on the files you want right away instead of waiting for all the files to be downloaded
 * Fault-tolerant operation - Airmtp will continuously retry any failed communication/transfer, resuming the download exactly where it left off, even in the middle of a file. This is important when downloading very large video files on marginal wireless connections


## One-Time Setup Requirements

### Nikon Cameras

By default your Nikon camera has an IP address of 192.168.1.1 and runs without encryption. You can modify both the IP address and wireless security via a one-time procedure using Nikon's Wireless Mobile Utility app (iOS and Android). Nikon has published instructions on modifying the security settings here. Modifying the IP address of your camera is useful if you run a typical network configuration that has the router at 192.168.1.1, which conflicts with the camera and makes it impossible to use a wired connection to your router/Internet at the same time you'd like to download from the camera. Here are instructions for the one-time procedure to change your cameras IP address:

 1. Install the Nikon Wireless Mobile Utility (WMU) app on your phone (iOS and Android).
 2. Turn your camera's WiFi on and then have your phone/tablet connect to that Network (Nikon's network usually starts with "Nikon\_", such as "Nikon\_WU2\_52A670FB7F45"
 3. Run WMU and click the gear icon at the top-right of the main screen to get to the Settings page.
 4. Click "WMA Settings" on the Settings Page.
 5. Click "Advanced Settings" on the WMA Settings Page.
 6. On the Advanced Settings Page, click on the DHCP Server IP address and change the subnet. For example, change it from the default of 192.168.1.1 to 192.168.2.1. Then click the DHCP client IP address and change it to the same subnet. For example, from 192.168.1.2 to 192.168.2.2.
 7. You're done. Enter the new DHCP Server IP address in the Camera IP address field of Airmtp (192.168.2.1 in this example).

### Sony Cameras

To enable wireless transfer-to-desktop functionality Sony cameras require a one-time configuration setup that must be performed with the camera attached to the computer via USB. You'll see this message if you haven't done the configuration. For Windows the setup is performed using Sony's PlayMemories Home application. For OSX the setup is done using Sony's Wireless Auto Import application. Sony doesn't provide a Linux application but if you can get access to a Windows or OSX machine you can perform the one-time setup on that system and then use Airmtp under Linux thereafter, even on a system other than the one in which you authenticated via the one-time setup using Sony's software.

Here are the one-time setup instructions:
#### Enable Sony Wireless transfers (OSX via Sony's Wireless Auto Import Application)

 1. Install Sony's Wireless Auto Import application and launch it from your Applications folder.
 2. Go to the USB Connection option in your camera's setup menu and set it to MTP, then connect the camera to a USB port on your computer.
 3. Launch the Wireless Auto Import application and press the 'Set' button on the Main Window.
 4. When complete you should see a dialog stating that your computer has been set as the Wireless Import Device. With Sony's application now installed and the camera activated your Mac will automatically transfers images from your camera using Sony's Wireless Auto Import application whenever your camera connects to your networking using the Send to Computer option. Sony's Auto Import application is a bit slow and doesn't let you select which files to transfer, which is why Airmtp might be a better transfer solution for you. To use Airmtp on this system you'll have to drag the Sony Wireless Auto Import application from the Application Folder into the OSX trash can, otherwise Sony's application will intercept the camera before Airmtp has a chance to communicate with it.

#### Enable Sony Wireless transfers (Windows via PlayMemories Home)

 1. Install the PlayMemories Home Windows application.
 2. Connect the camera to your computer via USB.
 3. Launch the PlayMemories Home application. You may get a dialog asking you to temporarily switch the USB operation mode. Click 'Yes' if you get this prompt.
 4. You may get a dialog asking you to see options for cameras. Click 'No' if you get this prompt.
 5. Near the top-left of the PlayMemories window you should see your attached camera listed. Click the camera to bring up the camera settings options.
 6. Click 'Wi-Fi Import Settings' in the settings page.
 7. Click 'Custom' in the Wi-Fi Import Settings dialog.
 8. Click 'Set' in the dialog whose text reads This Computer must be set as the automatic Wi-Fi import destination for the camera.
 9. Click 'Next' to accept the Windows Firewall changes.
 10. You should see a dialog indicating that settings change completed.
 11. Your camera is now configured to allow wireless desktop transfers. By default your computer will automatically mount your camera whenever you use its Send to Computer feature, which utilizes Microsoft's built-in MTP-IP driver to treat the camera as a storage device, allowing you to drag and drop files from the camera to your local folders. This feature is very slow and produces intermittent errors, which is why Airmtp might be a better transfer solution for you. You'll need to disable auto-mounting of the camera via another one-time process (instructions below) - uninstalling PlayMemories Home will not disable the auto-mounting feature. Until you have disabled auto-mounting Airmtp will be unable to communicate with the camera because the auto-mounting driver will intercept the camera when it becomes available over WiFi, making it unavailable for other wireless clients like Airmtp.

#### Disabling Auto-Mounting of Sony camera on Windows

 1. To disable auto-mounting you must allow your system to mount the camera once so that it shows up in the Device Manager of the Windows Control Panel, where it can then be disabled for all future mount attempts. For the camera to show up on your system its wireless settings must be configured, which is also required to use Airmtp. See the instructions below.
 2. With the camera disconnected from USB, go to your camera's wireless menu and click Send to Computer. After the camera establishes its connection to the router you should see a screen indicating that it's attempting to connect to your computer, listing the name of the machine you configured in PlayMemories Home and the SSID of your wireless router.
 3. Wait for your computer to discover the presence of your camera over WiFi. This might take up to a minute. When discovered your computer will either display an auto-play dialog asking what action to take with the camera, or failing that, an icon representing the camera within your windows filesystem. If neither of these happens and your computer fails to discover the camera then your done with this process (ie, for whatever reason the auto-mounting isn't working and since the goal is to disable auto-mounting there's nothing more for you to do).
 4. Run the Windows Control Panel's Device Manager. For example in Windows 7 you can do this by clicking the Start Menu and typing "Device Manager" and clicking the search result associated with Device Manager.
 5. In Device manager look for the icon in associated with the camera. On my Windows 7 system it shows up under the portable devices category.
 6. Right-click on the camera and click 'Disable' from the popup menu. The icon representing the camera within your windows filesystem should now disappear - and should not reappear in the future when you perform a Send to Computer operation from the camera. The camera's icon will still appear within the Device Manager whenever the camera is available, but with a greyed-out tag indicating that the device is disabled. If you ever want to re-enable the Microsoft MTP-IP driver, perform a Send to Computer on the camera so that the icon shows up in the Device Manager and then right-click on the camera and click 'Enable'.

#### Sony Wireless Setup

Sony's Send to Computer functionality requires that you perform a one-time wireless setup on your camera. Unlike the 'Send to Smartphone' feature where the camera creates its own ad hoc wireless network that you connect to, the Send to Computer' feature requires that the camera connect to your existing wireless network/router. Here are the steps to perform this one-time wireless setup on your camera:

 1. Go to your camera's wireless menu and click the Access Point Set option.
 2. Select the network name of your home/work wireless network from the list of networks presented by the camera.
 3. If your network is password-protected, click on the input line of the password field to bring up the password-entry screen and enter your network's password.
 4. The next screen lets you select the IP address method (Auto or Manual) and the 'Priority Connection' setting. Set 'Priority Connection' to ON - this will allow the camera to automatically connect to this network whenever you perform Send to Computer operations from the camera. For IP address Airmtp supports the 'Auto' method, where Airmtp will search the network every time it runs and automatically detect the IP address of your Sony camera via the SSDP Discovery protocol. However, SSDP Discovery may not work on all systems so if Airmtp is failing to discover your Sony camera then use the Manual IP address method instead - for example, if your router is configured at IP address 192.168.1.1 your manual settings might look like this, where the camera is configured for IP address 192.168.1.10 - be sure to select an IP address that's not within the range of IP addresses that your router's DHCP server will use. Set the default gateway to the IP address of your router. The subnet mask should usually be set to 255.255.255.0
 5. The camera will now attempt to connect to your wireless network to confirm that your settings (including the wireless password) are correct. Once confirmed you should see a screen indicating that the network is registered.
 6. When using Airmtp, if you chose "Auto" as the IP address mechanism during the camera's wireless setup then enter "Auto" in the IP address field of Airmtp, otherwise enter the static IP address you chose for the camera.

#### Important note regarding ony 'Send to Computer' and transfer sessions

Each use of the camera's Send to Computer function supports only a single wireless session with a client like Airmtp. For Airmtp a wireless session is defined as anytime you press the 'Start Download' or 'Preview File List for Criteria', including all files that Airmtp downloads/lists as part of that session. When the wireless session to the camera is over Airmtp will automatically send a command to the camera to take it out of the Send to Compute (and put the camera into sleep mode), provided the session terminates cleanly (ie, you don't press <ctrl-c> within the command window to abort the session early). If the session does not terminate cleanly/properly then the camera will stay in the Send to Computer mode after Airmtp's session has ended - because this mode only supports a single wireless session any future connection attempt from Airmtp will be unsuccessful. To resolve this you will have to manually cancel out of the the Send to Computer mode on the camera and then re-enter the mode again.

#### Canon Cameras

Canon cameras support SSDP Discovery, which allows Airmtp to automatically discover the IP address of your camera when you've set the camera's IP address to "Auto". Simply type "Auto" for the Camera IP address field in Airmtp. However, SSDP Discovery may not work on all systems so if Airmtp is failing to discover your camera then use the Manual IP address method instead. Canon supports both ad hoc and infrastructure modes - for ad hoc the camera creates its own wireless network that you connect your computer - for infrastructure the camera connects to your existing home/work wireless network. In ad hoc mode Canon cameras typically use a fixed IP address of 192.168.1.2. For infrastructure mode Canon lets you specify either 'Auto' or a static IP address of the camera. When using a static IP address make sure to select an address outside the range of DHCP addresses that your router is configured to supply. For example if the DHCP range of the router is 192.168.1.100 to 192.168.1.200 then select an IP address below 192.168.1.100 or above 192.168.1.200 (don't pick 192.168.1.1 because that is likely the address of your router). For this example you can use 192.168.1.20, with a subnet mask of 255.255.255.0 and a default gateway of 192.168.1.1 (gateway is the router's IP address).

After you create the wireless configuration on your Canon camera, the camera will usually wait for a connection from a wireless client (Airmtp in this case) to complete the configuration, which then associates that specific client to the wireless configuration/set. If you have an existing wireless configuration that you've used with other non-Airmtp clients then you'll have to recreate the setup to allow the camera to associate the configuration with Airmtp.

#### Optimizing Wireless Download Performance

If you are using a camera that connects to your existing wireless network in infrastructure mode rather than creating its own ad hoc wireless network then your wireless performance may reach only half its potential because two nodes on an infrastructure network can't communicate directly like they can on an ad hoc wireless network - this means that all data from the camera to your computer must make two trips, one from the camera to your wireless router and another from the router to your computer. This applies to all Sony cameras in 'Send to Computer' mode and Canon cameras where you've elected to use infrastructure mode instead of ad hoc. You can avoid this double-trip penalty by using a wired connection from your computer to the router - that way the data from the camera only has to take one trip over your wireless network.


## User's Guide (Graphical Interface)

The best resource for learning how to use Airmtp is the Youtube tutorial linked at the top of this page.

### Basic Operation

Airmtp provides two basic methods for selecting which images/movies to download - in the camera or on your computer. The benefit of selecting in the camera is that you can visually preview the images(s) first. The downside is that it's more cumbersome to select a large number of images. Also, some models limit the types of files you can select within the camera. For example the D7200 doesn't allow video files to be selected. Consumer-level cameras like the Nikon 1 J4 only let you select JPEGs. Fortunately both raw and video files can be downloaded on all camera models using the computer selection method within Airmtp.

Airmtp is really two separate applications - a Graphical Interface (airmtp) and a Command-Line program (airmtpcmd). The graphical interface lets you to visually specify your download options, which are then passed to airmtpcmd to perform the actual downloads. You can optionally use the command-line program directly, which enables you to script/automate your downloads. See the Command Line Reference in this page for details.

Airmtp maintains a permanent download history of every file you transfer. Airmtp uses this history to allow you to automatically skip over files you've already transferred, without having to specifically set a criteria that excludes those files. Airmtp's default behavior is to skip files that are in its download history; you can override this behavior by unchecking the "Skip images/movies you've previously downloaded" option in each of the dialogs.

The Airmtp GUI tries its best to be intuitive by remembering all the options you specified on your last download, along with the last 32 directories you've used. These options are saved every time you initiate a download operation.

### Selecting images in the camera (only supported on Nikon cameras)

 1. Click the "Select in Camera" button on the Main Application Dialog, which will bring up the Select in Camera dialog.
 2. On your camera, find the menu location where files can be selected for upload, which varies depending on model. You should look for the option that reads similar to "Select for Upload" or "Select to send to smart device" or "Send to smartphone", etc... The Media Transfer Protocol (MTP) interface that Airmtp uses to communicate with the cameras is principally oriented for sending images to smartphones, which is why you may need to look for the "Send to smartphone" option on your camera even though you'll be sending the images to your computer running Airmtp. Some cameras also allow you to select images in the playback menu, including the Nikon D7200 and D750 - what's nice about these models is that the selections persist across camera power cycles, which means you can select images as you're shooting across multiple days and then use Airmtp to download your selected images all at once.
 3. Once you've located your camera's menu that allows choosing files to upload, select one or more files in the camera using the button shortcuts depicted on your camera's screen. For example on the Nikon D7200 the button is the zoom-out key; on the Nikon J4 it's the bottom button of the circular multi-selector.
 4. When you've finished selecting which files to upload your camera will either let you proceed directly to enabling its WiFi (Nikon J4 allows this by pressing the OK button on the multi-selector), or it may require you to enable the WiFi as a separate step (Nikon D7200). Use whichever method is available to enable the camera's WiFi
 5. Once the camera's WiFi is enabled you should see its SSID in the available wireless networks on your computer. Nikon prefixes their SSID with "Nikon_", for example "Nikon_WU2_52A670FB7F45". Connect to the camera's network on your computer by selecting its SSID. Ideally you'd like to configure your computer to automatically connect to your camera's WiFi whenever it's available, although not every operating system may support this. Windows supports this - please read the wireless setup instructions on this page for details.
 6. In the 'Select in Camera' dialog, set your output directory. The default directory is the one specified when you last used Airmtp. If this is the first time you're using Airmtp then the default directory will be your home Pictures directory (/users/yourusername/Pictures). Airmtp remembers the most recent directories you've used in Airmtp (up to 32), sorted by how recently you used each directory. If the directory you want is not already in the list you can click the 'More choices' button to summon a directory navigation dialog that will allow you to either navigate to your directory of choice or enter a directory path manually.
 7. Set how you'd like Airmtp to handle filename conflicts, ie what you'd like Airmtp to do if it encounters any files on your system with the same name as the ones you've selected to download. By default Airmtp will create a unique filename for any incoming files whose names conflict with existing files. The full options are:
        * generate unique filename - a unique filename will be generated by adding a -new-x suffix, where 'x' is the first non-used numerical suffix for files in the directory. For example, DSC_1256.NEF becomes DSC_1256-new-1.NEF. If that file also exists the name becomes DSC_1256-new-2.NEF, etc
        * overwrite file - existing file will be deleted at the start of the download
        * skip file - file will be skipped (not downloaded)
        * prompt for each file - you'll be prompt for the action to take for each filename conflict
        * exit - Airmtp will terminate
 8. By default Airmtp will skip over images/movies you've downloaded from the camera on a previous session. You can override this behavior by unchecking the "Skip images/movies you've previously downloaded" option, which will cause Airmtp to ignore its download history.
 9. If you'd like to enter realtime transfer mode after the download of your in-camera selected images has completed (ie, transfer images from the camera as you take them), set 'Realtime download' to 'normal download then realtime'.
 10. Click the 'Start Download' button to begin the transfer. Airmtp will launch airmtpcmd in its own terminal window - airmtpcmd is the command-line utility that handles all communication with the camera, including the downloads. airmtpcmd will report the progress of its operations in its terminal window, exiting when it's complete, or when it encounters what it believes is an unrecoverable error, or if you cancel the transfer by press <ctrl-c>
 11. After airmtpcmd exits, Airmtp will display a transfer report that contains all the progress information generated by airmtpcmd. For brevity the report excludes information about files that were skipped due to being in the download history (ie, files skipped because you previously downloaded them). If you'd like to see when the skipped files were previously downloaded and to what location, set the Logging: option to 'verbose' before clicking 'Start Download'


### Selecting images by criteria on the computer (Nikon, Canon, and Sony cameras)

 1. Enable WiFi on your camera. For Canon cameras you can use either an ad hoc wireless network created by the camera or have the camera connect to your existing wireless network. For Sony cameras you enable WiFi transfer mode via the Send to Computer option in the camera's wireless menu.
 2. Launch Airmtp if you haven't already done so and click the "Select on Computer" button on the Main Application Dialog, which will bring up the Select on Computer dialog.
 3. By default Airmtp will download every image/video file on the camera, except for those you've previously downloaded. The 'Select on Computer' dialog lets you to establish any combination of criteria that then limits which of those files get downloaded.
 4. The 'File Types' section lets you choose which types of files are downloaded, based on the extension of the file. The built-in types are NEF, JPG, TIF, MOV, and CR2. If your camera supports a type not listed you can enter its extension in the 'More:' field that is positioned next to the built-in types.
 5. The 'Capture Date' section lets you limit which files are downloaded based on a capture/acquisition date. You can choose from either the preselected set of dates (today, yesterday, past week, past month, past year), or enter a custom date range. For the custom date range you can enter a starting date, ending date, or both. Each date must be in the format of mm/dd/yy and include leading zeros - for example, "05/02/12". You an optionally include a time specification as well, in the form of hh:mm:ss - for example, "05/02/12 15:35:15". When you specify a starting date without a time, the time will be assumed to start from midnight. When you specify an ending date without a time, the time will assumed to end at 23:59:59. For example, a starting date of 04/05/12 and ending date of 04/10/12 will download all files captured on or after 04/05/12 at midnight and on or before 04/10/12 23:59:59.
 6. The 'Media Card' section lets you specify which media card slot on the camera will be used as the source of the images to download. By default Airmtp will use the first populated card slot it finds, starting from the first slot. You can optionally override this by specifying a particular slot. You can also download from both media cards for cameras with dual-card support; however this method is not recommended when you have the second slot configured for backup mode because it will cause Airmtp to download the same image twice.
 7. The 'Download Order' option lets you to specify the chronological order by which files are downloaded (by capture-date). The choices are oldest-first or newest-first. This option doesn't limit which files are downloaded, only the order by which they're downloaded. This is useful when you'd like to start working on more recently taken images/movies right away (as they download), rather than waiting for the download of all the files to complete.
 8. The 'Output Directory' section lets you specify where the downloaded files will be placed. The default directory is the one specified when you last used Airmtp. If this is the first time you're using Airmtp then the default directory will be your home Pictures directory (/users/yourusername/Pictures). Airmtp remembers the most recent directories you've used in Airmtp (up to 32), sorted by how recently you used each directory. If the directory you want is not already in the list you can click the 'More choices' button to summon a directory navigation dialog that will allow you to either navigate to your directory of choice or enter a directory path manually.
 9. The 'If File(s) Exist' section lets you specify how Airmtp will handle filename conflicts, ie what you'd like Airmtp to do if it encounters any files on your system with the same name as the ones you've selected to download. By default Airmtp will create a unique filename for any incoming files whose names conflict with existing files. The full options are:
        * generate unique filename - a unique filename will be generated by adding a -new-x suffix, where 'x' is the first non-used numerical suffix for files in the directory. For example, DSC_1256.NEF becomes DSC_1256-new-1.NEF. If that file also exists the name becomes DSC_1256-new-2.NEF, etc
        * overwrite file - existing file will be deleted at the start of the download
        * skip file - file will be skipped (not downloaded)
        * prompt for each file - you'll be prompt for the action to take for each filename conflict
        * exit - Airmtp will terminate
 10. The 'Additional Args' section lets you specify additional command line arguments to be passed to airmtpcmd. These can be options that allow for additional selection criteria and/or options that control the general operation of airmtpcmd. See the Command Line Reference section on this page for a full list of arguments.
 11. The 'Skip images/movies you've previously downloaded' option allows you to control whether Airmtp should skip (ie, not download) files you've previously downloaded from the camera.
 12. If you'd like to enter realtime transfer mode after the download of your in-camera selected images has completed (ie, transfer images from the camera as you take them), set 'Realtime download' to 'normal download then realtime'.
 13. With your criteria now set, you can either click 'Start Download' to perform the transfer or 'Preview File List for Criteria' if you'd first like to see a directory listing of files on the camera, filtered by your criteria. Note that the list will include files you've already downloaded even if you've checked the 'Skip images/movies you've previously downloaded' option; however, those files will not be re-downloaded once you click 'Start Download' (unless you've unchecked the option).

### Realtime Downloads

Airmtp supports a realtime download mode, where it will transfer images from your camera as you shoot them. Only certain camera models support taking photographs while in the WiFi mode used by Airmtp - see the camera feature matrix here for details. Even if your camera doesn't support taking pictures while WiFi is enabled you can still achieve faux-realtime transfers (termed 'staged realtime') by taking pictures with WiFi off and turning your camera's WiFi mode on - when Airmtp detects the camera it will automatically transfer the images you've taken. You can tell when the staged transfers are done on Sony cameras by waiting for the Send to Computer screen to go away - Airmtp actually puts the camera into sleep mode after the downloads complete, which conserves battery life if you leave the camera unattended after enabling WiFi. For other camera models you can watch the SD/CF access light (usually green) and wait for it to stop flickering, indicating that the transfers are done. You can then turn WiFi back off and resume shooting. You don't have to wait for the transfers to complete before turning WiFi back off - if you turn WiFi off in the middle of a transfer Airmtp will remember which image it was downloading when it lost the WiFi connection to the camera and then resume downloading from that point when the camera's WiFi is available again. This process can be repeated any number of times while Airmtp is running. You can also use this staged process on cameras that support actual realtime shooting as well, for example if you want an opportunity to review/delete images before they're transferred by Airmtp , or to conserve battery life by keeping WiFi off most of the time, or if you're taking photos at a far distance from the computer/router and WiFi reception will be poor and slow. Staged transfers are particularly useful on Nikon cameras using external WU-1a/WU-1b WiFi adapters because that setup disables access to the image review function while the WiFi adapter is enabled, so the only way to review images before they're transferred is by disabling WiFi. Canon bodies let you review images while in WiFi mode and let you delete image(s) as well - if you delete an image that Airmtp is actively transferring then Airmtp will detect the deletion and skip to the next file.

As part of Airmtp's staged download support the camera does not have to be powered on (or its WiFi enabled) when you start the realtime download mode. Simply press the 'Start Download' within Airmtp and it will enter a connection loop waiting for the camera to become available. However on Canon and Nikon cameras the realtime mode will launch faster if the camera is available when 'Start Download' is pressed (this allows Airmtp to avoid the initial download of file information at the start of realtime mode).

When using the realtime download mode your camera's clock must be synchronized with the system clock of your computer - this is necessary because Airmtp uses the timestamp of the images you taken to establish which images were shot in realtime (ie, shot after you started Airmtp). Failing to keep the clock's synchronized means either Airmtp will skip over the realtime images you take (if the camera's clock is running behind your system clock) or transfer images that were taken before you started Airmtp (if the camera's clock is running ahead of your system clock). Fortunately Airmtp automatically synchronizes the camera's clock on most Nikon and Canon cameras - you only need to assure that the camera's time zone and DST setting (Daylight Savings Time for USA users) are matched between camera and system, as these attributes aren't programmable over the WiFi connection.

You can use the realtime download mode either in combination with the normal transfer mode or by itself in a realtime-only mode. When used in combination with the normal transfer mode Airmtp will first transfer all the images that match your selected criteria, then enter the realtime download mode when those transfers are complete. This allows you to transfer images you already have on the camera while shooting new, realtime images as well - in other words, you can start shooting new images immediately without waiting for the download of the existing images to complete. When configured for realtime-only mode Airmtp will ignore any existing images you have on the camera and only download images that were taken after Airmtp is started (specifically, after the 'Start Download' button is pressed).

Regardless of which realtime mode you use, Airmtp will apply the selection criteria you specified in the dialog for realtime downloads the same as it does for normal downloads (the only exception is the capture date criteria, which naturally doesn't apply to realtime downloads since you're instructing Airmtp to transfer images taken now). For example if you've configured Airmtp to only download JPG files but have the camera configured for raw+JPG, Airmtp will only download the JPG files shot in realtime. The same applies to the 'Media Card' configuration - if your camera has dual media slots but you've configured Airmtp to only download images from slot #2, Airmtp will only download realtime images that the camera saves to slot #2.

By default Airmtp will poll the camera every 3 seconds to check for new images to download. This interval was selected to strike a reasonable balance between responsiveness and battery life. You can modify the polling interval via the --realtimepollsecs option. Use a shorter interval if you'd like Airmtp to respond to new images faster, or a longer interval to increase battery life. Any value above 30 seconds will likely cause the camera to drop the WiFi connection due to an inactivity timeout - for very long polling intervals I suggest turning the camera's WiFi off/on during shooting so that you can manually decide when images should be transferred.

See the Download Exec section below for optionally launching an image viewing application for each downloaded file, which is especially useful for realtime downloads.

### Download Exec

Airmtp can optionally launch an application of your choice for each file downloaded, in both normal or realtime download modes. For example you can automatically launch an image review application to display each image as it's downloaded. This feature is accessed via the --downloadexec command option, which can be entered in the 'Additional Args' field of the GUI. The behavior of downloadexec can be further configured via --downloadexec_extlist (to limit which file types your application is launched for and downloadexec_options (various options such as waiting for the launched app to complete before continuing to next download).

When launching an image viewing application via downloadexec you'll typically want to configure the application for single window/instance operation (if supported) - that way each downloaded image will be displayed in the same window instead of creating a bunch of separate windows.

Here are some sample command-line recipes for various popular image viewing applications. For best results you should copy 'n paste these sample commands lines rather than typing them yourself.

FastStone Image Viewer - Microsoft Windows (link)
By default FastStone operates in single-window mode when launched by Airmtp. To configure the window in which the image is displayed go to to Settings -> 'Associated images launches in' and choose one of the following per your preference 'Full Screen', 'Browser View', 'Windowed View'.
32-bit Windows: --downloadexec "C:\Program Files\FastStone Image Viewer\FSViewer.exe" @pf@
64-bit Windows: --downloadexec "C:\Program Files (x86)\FastStone Image Viewer\FSViewer.exe" @pf@

Irfanview Image Viewer - Microsoft Windows (link)
By default Irfanview operates in multi-window mode. To configure single-window mode go to Options -> Properties/Settings... -> Start/ Exit options -> 'Only 1 instance of Irfan View is active'. Note that Irfanview doesn't support raw images so --downloadexec_extlist JPG is included in these sample command lines:
32-bit Windows: --downloadexec "C:\Program Files\IrfanView\i_view32.exe" /file=@pf@ --downloadexec_extlist JPG
64-bit Windows: --downloadexec "C:\Program Files (x86)\IrfanView\i_view32.exe" /file=@pf@ --downloadexec_extlist JPG

FastRawViewer - Microsoft Windows (link)
By default FastRawViewer operates in multi-window mode. To configure single-window mode go to File -> Preferences -> Other -> 'Run single program instance'.
32-bit/64-bit Windows: --downloadexec "C\Program Files\LibRaw\FastRawViewer\FastRawViewer.exe" @pf@
64-bit Windows running 32-bit version of FastRawViewer: --downloadexec "C\Program Files (x86)\LibRaw\FastRawViewer\FastRawViewer.exe" @pf@

Image Preview - Mac/OSX (built-in application)
By default the OSX preview image operates in single-window mode.
Open using default viewing application (most systems this is Image Preview): --downloadexec open @pf@
Open using Image Preview specifically: --downloadexec open ~a Preview @pf@

FastRawViewer - Mac/OSX (link)
By default FastRawViewer operates in multi-window mode. To configure single-window mode go to File -> Preferences -> Other -> 'Run single program instance'.
--downloadexec /Applications/FastRawViewer.app/Contents/MacOS/FastRawViewer @pf@

Eye of GNMODE (eog) - Linux (included with most Linux distributions - link)
--downloadexec eog ~~single-window @pf@


### File Renaming Engine

Airmtp allows you to customize the names of directories and filenames for the images you download via a simple, mini-scripting language, accessible via the the --dirnamespec and --filenamespec command line options. You can enter these options in the 'Additional Args' field of the GUI. Below are some examples to help get you started.

Include the model of the camera in the downloaded filename.
Sample Output: D7200_DSC_0119.NEF
--filenamespec @cameramodel@_@filename@

Create a directory based on the capture date of each file and a filename based on the sequence number of each download (ie, first download seq # is 0001, second is 0002, etc..).
Sample Output: 20150928\Photo-0001.JPG
--dirnamespec @capturedate@ --filenamespec Photo-@dlnum@.@filename_ext@

Include a custom name for the camera based on the serial number. For example if you have two cameras, one with S/N 7104765 and another with 5462197 and you'd like images from the first camera to have "MyCamera" in the name and images from the second to have "JillsCamera". Note that the S/N Airmtp uses is the one the camera reports via the wireless interface, which may have more or fewer digits than the S/N printed on the camera - you can view the serial number that Airmtp uses in a download transfer report.
Sample Output: MyCamera_DSC_1125.NEF, JillsCamera_DSC_2535.NEF
--filenamespec @cameraserial@@replace~7104765~MyCamera@@replace~5462197~JillsCamera@_@filename@

## FAQ - Frequently Asked Questions

Q: Sometimes during extended transfer sessions airmtpcmd reports a MTP_RESP_StoreNotAvailable error and exits. Why is that?  
A: Cameras have a data-integrity mechanism that disables access to their SD/CF cards when the battery is low. This is done to prevent incomplete writes in case the battery charge runs out while the camera is writing to a card.

Q: My camera has a WiFi option but it wont let me enable it (it's greyed out)  
A: The mostly likely cause is low battery charge - for example Nikon bodies wont let you enable WiFi when the battery is low. There also might be a configuration setting in the camera that is incompatible with WiFi operation. On Nikon bodies the camera wont let you use WiFi when the HDMI port is in use.

Q: I have a wired connection to my router and whenever I try to connect wirelessly to my camera Airmtp reports "A device at 192.1681.1.1 responded but the connection was refused. This is likely because you are connected to a normal WiFi network instead"  
A: The default IP address of most routers is 192.168.1.1, which unfortunately is also the default IP address of the wireless network created by Nikon cameras. Even though you have separate a wired connection to your router there can only be one device with a given IP address and so when you attempt to connect to your camera at 192.168.1.1 you'll be connecting to your router instead. Fortunately changing the IP address of your Nikon camera is easy - see the instructions here.

Q: My wireless download performance is only half the 2 - 2.5 MB/s that Airmtp is quoted to achieve. I'm getting around 1 MB/s for my downloads.  
A: If your camera uses the wireless infrastructure mode then you'll need to use a wired connection to your router to achieve 2 MB/s. See details here.

Q: Whenever airmtp runs it changes my camera's clock to the wrong time.  
A: Airmtp synchronizes the camera's clock to your system's UTC time. The time that the camera displays is then localized to the time zone and DST setting (Daylight Savings Time for USA) that you configured in the camera. If the camera's time zone and/or DST is not matched to your system's time zone/DST then the time will appear incorrect. If you'd prefer for Airmtp to not synchronize your camera's clock then add "---maxclockdeltabeforesync disablesync" (without the quotes) to the command line.

## Command Line Reference

**airmtpcmd.exe (Windows) or airmtpcmd (Linux) or airmtpcmd.py (Windows/OS X/ Linux running source through Python interpreter) \[optional args\]**

When run with no options Airmtp's default behavior is to either download
every image that has been selected for download by the user on the
camera's playback menu or, if no images were selected on the camera, to
download every image/movie file it finds on the first populated memory
card in the camera located at IP address 192.168.1.1 (Nikon's default IP
address), storing the files into the current directory and skipping any
files downloaded on previous invocations. Any name collisions with
existing files will be resolved by generating unique filenames by adding
a -new-x suffix (for example, DSC\_1575.nef becomes DSC\_1575-new-1.nef,
DSC\_1575-new-2.nef, etc...). Optional command-line arguments can be
added to set the criteria of which files to download, where they should
be downloaded, how filename collisions should be resolved, and other
general behavior of the application.

All argument names are case sensitive but the optional values for each
argument are case-insensitive. For example "--extlist" must be undercase
but the actual extension list specified for that option can be any case
(an "--extlist jpg" will match both .jpg and .JPG extensions for camera
files).

You can abbreviate any argument name provided you use enough characters
to uniquely distinguish it from other argument names. For example, --a
in place of --action, if there are no other arguments that start with
--a.

**--help**\
Prints a help display listing all the typical options supported

**!filename** (changed from '@filename' to '!filename' in v1.1)\
Load additional arguments from a text file. In addition to any parameter
files you specify, airmtpcmd will always load a file named
'airmtpcmd-defaultopts' in its working directory if it exists (for
Windows/Linux Airmtp will look for this file in the directory Airmtp was
installed to; for OSX it will be in
/Applications/airmtp.app/Contents/Resources). The parameters from the
default file will be loaded first, allowing you to override them with
parameters from your own files and those specified on the command line.
All parameter files must be formatted so that each parameter word is on
a separate line, which is a requirement of Python's argparse routine.
For example:

       --action
        getsmallthumbs
        --extlist
        NEF
        JPG

**--ipaddress address | auto** ("auto" IP address support for Sony added
in v1.1)\
Specifies the IP address of the camera supporting the MTP-IP interface.
If not specified the default is 192.168.1.1, which is the default for
most Nikon cameras (although some of the newer cameras ship with a
default of 192.168.0.1). On Canon the ad hoc wireless address is usually
192.168.1.2. Canon also supports wireless infrastructure mode, where
instead of the camera serving as a temporary WiFi access point it can
use an existing wireless network - for this mode you can configure the
camera to any IP address you'd like. Sony cameras support only
infrastructure mode, where the camera connects to your existing wireless
network/router - the camera lets you choose either a manual IP address
or Auto (DHCP-assigned) - if you choose the latter, specify --ipaddress
auto and airmtp will attempt to discover the camera's IP address using
the [Simple Service Discovery Protocol
(SSPD)](https://en.wikipedia.org/wiki/Simple_Service_Discovery_Protocol).
SSDP doesn't work on all systems so if airmtp has trouble locating your
Sony camera trying configuring the camera for a manual IP address
instead.

**--action** \[getfiles | getlargethumbs | getsmallthumbs | listfiles\]\
What action to perform. The default action 'getfiles' will download the
full-sized version of the files. 'getlargethumbs' will download the
large thumbnail of each image/video. 'getsmallthumbs' will download the
small thumbnail of each image/video. Not all cameras support both large
and small thumbnail downloads. 'listfiles' will generate a directory
listing of files on the camera, sorted by the --transferorder option.

**--realtimedownload** \[disabled | afternormal | only\] (added in
v1.1)\
Download images in realtime as they're taken. The default is disabled,
which means only the action specified by --action is performed.
'afternormal' means airmtp will enter realtime download mode after
downloading any images specified by --action . 'only' means airmtp will
enter realtime download mode immediately and not download preexisting
images on the camera. All criteria options such apply to the normal and
realtime download modes except those that aren't applicable once
realtime mode begins, such as --startdate and --enddate. When using
realtime download make sure your camera's clock is synchronized to your
system clock because airmtp sometimes relies on timestamps to
distinguish between realtime photos and those already on the camera. For
Nikon and Nikon cameras airmtp automatically synchronizes your camera's
clock to the system clock every time airmtp runs - however even with
this automatic synchronization you must still make sure the camera's
time zone and DST setting (Daylight Savings Time for USA) match your
system's settings. For other cameras you'll want to make sure your
camera clock is synchronized. The frequency at which airmtp checks the
camera for realtime images can be controlled via --realtimepollsecs.

**--extlist** \[extension ...\]\
Specifies which types of files (by extension) to download/list. If not
specified airmtp will download/list every file found. Multiple
extensions can be included. Example: extlist NEF JPG MOV. In the
unlikely case where a camera has downloadable files without extensions,
include &lt;noext&gt; in the extlist to download those files as well.

**--startdate and --enddate** \[mm/dd/yy\] or \[mm/dd/yy hh:mm:ss\]\
Selects the starting and/or ending creation-date criteria of files to
download/list. There are two specifications supported - date-only or
date+time. The dates/time is inclusive - any file created on or after
startdate will be included; any file created on or before enddate will
be included. Examples:

> **--startdate 05/06/15** (download all files created on or after
> 05/06/15 00:00:00)
>
> **--enddate 09/07/15** (download all files created on or before
> 09/07/15 23:59:59)
>
> **--startdate 05/06/15 --endddate 09/07/15** (download all files
> created on or after 05/06/15 00:00:00 and before 09/07/15 23:59:59)
>
> **--startdate 05/06/15 15:05:10** (download all files created on or
> after 05/06/15 3:05:10 PM)

**--outputdir** \[directory\]\
The directory to store the downloaded files. The directory must already
exist. Put quotes around the directory if it contains spaces. Example:
outputdir "c:\\My Documents". The default is the current working
directory. If both --outputdir and --dirnamespec are specified then
airmtp uses --outputdir as the base directory and the directory name
generated from --dirnamespec will be relative from that base directory.

**--ifexists** \[uniquename | skip | overwrite | prompt | exit\]\
Specifies what action to take if a local file exists in the output
directory matching a file to be downloaded. The default 'uniquename'
will cause a unique filename to be generated by adding -new-x suffix
(for example, DSC\_1575.nef becomes DSC\_1575-new-1.nef,
DSC\_1575-new-2.nef, etc...). 'skip' will cause the file to be skipped
and not downloaded - be careful when using this option without the
--camerafolderinoutputdir option, because if the same root filename
exists in multiple folders on the camera then this will cause the file
in all folders but the first to be skipped. 'overwrite' will overwrite
the local file with the downloaded file - the same caution as 'skip'
applies regarding the same file in multiple camera directories. 'prompt'
will present a choice of actions to take on the console
(uniquename/skip/overwrite/prompt/exit). 'exit' will cause the
application to terminate whenever an existing file with the same name as
a download candidate is found - note that the existence check of a given
file is performed just before the download begins.

**--downloadhistory** \[skipfiles | ignore | clear\]\
Controls how the file download history is handled for this invocation.
Airmtpcmd maintains a database of all files it has downloaded for a
given camera model/serial number combination. Each file in the database
is identified by the combination of its name, creation date, and size;
these three elements together allow Airmtp to guarantee against false
positives/negatives of the history. The default 'skipfiles' will skip
any file that is in the download history. 'ignore' will cause airmtpcmd
to ignore the download history for this invocation when deciding whether
to download a given file - ie, it will download files even if they're in
the download history. Note that the download history will still be
updated for any files downloaded during '**ignore**' invocations; this
allows the history to be utilized on future invocations when 'ignore' is
not specified. 'clear' will delete the entire download history for the
connected camera model/serial number at the start of execution; the
download history will still be updated for any files downloaded during
the session.

**--onlyfolders** \[folder ...\]\
List of folders ****on the camera from which to download from. Any
downloadable file(s) found that **are not in** one of the list folders
will not be downloaded/listed. Example: onlyfolders 100D7200 101D7200.
The default is to download/list from any folder on the camera. In the
unlikely case where a camera has downloadable files in the root
directory, include &lt;root&gt; in the list to download those files as
well. Be careful when using this option with realtime downloads because
when a camera folder reaches its maximum file capacity the camera will
create a new folder to store images and if that new folder is not
included in your --onlyfolders list then any realtime images stored in
that new camera folder will be excluded and not downloaded.

**--excludefolders** \[folder ...\]\
List of folders on the camera from which to not download from. Any
downloadable file(s) found that **are in** one of the list folders will
not be downloaded/listed. The default is to not exclude any folders. In
the unlikely case where a camera has downloadable files in the root
directory, include &lt;root&gt; in the list to exclude the the download
of those files as well.

**--transferorder** \[oldestfirst | newestfirst\]\
Controls the order of which files are downloaded/list, based on their
creation dates. When 'oldestfirst' is specified the oldest file on the
camera will be downloaded/listed first, then the next oldest, etc...
When 'newestfirst' is specified the newest file on the camera will be
downloaded first, then the next newest, etc...

**--slot** \[firstfound | first | second | both\] ('both' option added
in v1.1)\
Determines which media slot/card on the camera will be selected to
download/list files from. The default 'firstfound', which will select
the first slot found populated with a media card. 'first' or 'second'
will select the first or second slot respectively. 'both' will use both
media cards. If your camera has two card slots and you have them
configured in backup mode then specifying 'both' for slot is not
recommended because airmtpcmd's operation retrieve information about
files on the camera will take twice as long yet only half of those files
will be unique. If you still want to use 'both' in this configuration
then only one file of the mirrored pair will be downloaded if
--downloadhistory is set to 'skipfiles'. Using 'both' is also not
recommended for real-time capture when the cards are operating in backup
mode because the timestamp of the identical files across the two cards
is often skewed by one second, which will cause airmtpcmd to believe the
files are unique and defeat the download history file timestamp-matching
mechanism.

**--cameratransferlist** \[useifavail | exitifnotavail | ignore\]\
Controls how to manage a potential camera transfer list, which is the
list created by the camera when the user selects image(s) to download on
the camera's playback menu. When airmtpcmd runs it interrogates the
camera to see if a transfer list exists; the cameratransferlist controls
how airmtpcmd is to respond to the existence or non-existence of this
list. When 'useifavail' is specified airmtpcmd will only download images
within the transfer list, and will ignore all other selection criteria
specified by the other command line options. The download history will
still be utilized however, meaning any images previously downloaded will
be ignored, depending on the setting of the downloadhistory option. When
'exitifnotavail' is specified airmtpcmd will terminate if the camera's
transfer list is empty (ie, there are no user-selected images for
download), unless --realtimedownload is specified, in which case airmtp
will enter its realtime download mode instead of exiting. When 'ignore'
is specified airmtpcmd will ignore any potential transfer list on the
camera and will instead download/list all images on the camera based on
the criteria specified with the other command line options.

**--filenamespec** spec and **--dirnamespec** spec (added in v1.1)\
Rename downloaded files using Airmtp's renaming engine. Place spec in
quotes if it contains any literal spaces. This can be applied to the
filename and/or the directory (tree) where the file is stored. 'spec'
contains your desired output name including optional specifiers, which
offer the ability to insert dynamic data into the filename, such as the
camera model, serial number, capture date, etc.. Each specifier is
enclosed in @@ and can optionally include subscripts to only use a
portion of the dynamic data and also options to change elements such as
case. If you'd like preview/test your --dirnamespec and --filenamespec
before attempting a download then use --action listfiles. The directory
listing will show a preview of what the output directory/filename name
will look like. Here is the full format of a specifier; everything after
specifier name is optional:

@**specifiername**:**subscript\_start**:**subscript\_end**:**options**@

Here is the full list of support specifiers:
<table width="90%" border="1" cellspacing="0">
  <tr>
    <td width="16%"><strong>Specifier</strong></td>
    <td width="56%"><strong>Description</strong></td>
    <td width="28%"><strong>Example</strong></td>
  </tr>
  <tr>
    <td colspan="3" align="center"><strong>Capture Date/Time Specifiers</strong></td>
  </tr>
  <tr>
    <td>@capturedate@</td>
    <td>Capture date of file in yyyymmdd format</td>
    <td>20150924</td>
  </tr>
  <tr>
    <td>@capturedate_m@</td>
    <td>Capture date of file (month) in mm format</td>
    <td>09</td>
  </tr>
  <tr>
    <td>@capturedate_d@</td>
    <td>Capture date of file (day) in dd format</td>
    <td>24</td>
  </tr>
  <tr>
    <td>@capturedate_y@</td>
    <td>Capture date of file (year) in yyyy format</td>
    <td>2015</td>
  </tr>
  <tr>
    <td>@capturedate_dow@</td>
    <td>Capture date of file (day of week, numeric) [Monday=1, Tuesday=2...Sunday=7]</td>
    <td>4</td>
  </tr>
  <tr>
    <td>@capturedate_woy@</td>
    <td>Capture date of file (week of year) . Monday considered first day of week</td>
    <td>38</td>
  </tr>
  <tr>
    <td>@capturedate_month@</td>
    <td>Capture date of file (month, text)</td>
    <td>September</td>
  </tr>
  <tr>
    <td>@capturedate_dayofweek@</td>
    <td>Capture date of file (day of week, text)</td>
    <td>Thursday</td>
  </tr>
  <tr>
    <td>@capturedate_season@</td>
    <td>Capture season (Spring, Summer, Fall, or Winter)</td>
    <td>Fall</td>
  </tr>
  <tr>
    <td>@capturetime@</td>
    <td>Capture time of file in hhmmss format</td>
    <td>140513</td>
  </tr>
  <tr>
    <td>@capturetime_h@</td>
    <td>Capture time (hour) of file in hh format</td>
    <td>14</td>
  </tr>
  <tr>
    <td>@capturetime_m@</td>
    <td>Capture time (minute) of file in mm format</td>
    <td>05</td>
  </tr>
  <tr>
    <td>@capturetime_s@</td>
    <td>Capture time (seconds) of file in ss format</td>
    <td>13</td>
  </tr>
  <tr>
    <td colspan="3" align="center"><strong>Download Date/Time Specifiers. The airmtpcmd launch date/time is used as the download date/time for all files downloaded in the session</strong></td>
  </tr>
  <tr>
    <td>@dldate@</td>
    <td>Download date of file in yyyymmdd format</td>
    <td>20150924</td>
  </tr>
  <tr>
    <td>@dldate_m@</td>
    <td>Download date of file (month) in mm format</td>
    <td>09</td>
  </tr>
  <tr>
    <td>@dldate_d@</td>
    <td>Download date of file (day) in dd format</td>
    <td>24</td>
  </tr>
  <tr>
    <td>@dldate_y@</td>
    <td>Download date of file (year) in yyyy format</td>
    <td>2015</td>
  </tr>
  <tr>
    <td>@dldate_dow@</td>
    <td>Download date of file (day of week, numeric) [Monday=1, Tuesday=2...Sunday=7]</td>
    <td>4</td>
  </tr>
  <tr>
    <td>@dldate_woy@</td>
    <td>Download date of file (week of year) . Monday considered first day of week</td>
    <td>38</td>
  </tr>
  <tr>
    <td>@dldate_month@</td>
    <td>Download date of file (month, text)</td>
    <td>September</td>
  </tr>
  <tr>
    <td>@dldate_dayofweek@</td>
    <td>Download date of file (day of week, text)</td>
    <td>Thursday</td>
  </tr>
  <tr>
    <td>@dldate_season@</td>
    <td>Download season (Spring, Summer, Fall, or Winter)</td>
    <td>Fall</td>
  </tr>
  <tr>
    <td>@dltime@</td>
    <td>Download time of file in hhmmss format</td>
    <td>140513</td>
  </tr>
  <tr>
    <td>@dltime_h@</td>
    <td>Download time (hour) of file in hh format</td>
    <td>14</td>
  </tr>
  <tr>
    <td>@dltime_m@</td>
    <td>Download time (minute) of file in mm format</td>
    <td>05</td>
  </tr>
  <tr>
    <td>@dltime_s@</td>
    <td>Download time (seconds) of file in ss format</td>
    <td>13</td>
  </tr>
  <tr>
    <td colspan="3" align="center"><strong>Capture Filename/Folder/Media Card Specifiers</strong></td>
  </tr>
  <tr>
    <td>@pf@</td>
    <td>Shortcut to @path@/@filename@</td>
    <td>c:\pics\DSC_0014.NEF</td>
  </tr>
  <tr>
    <td>@path@</td>
    <td>Directory to local file (equal to --outputdir if no --dirnamespec, otherwise generated --dirnamespec for use by --filenamespec)</td>
    <td>c:\pics</td>
  </tr>
  <tr>
    <td>@filename@</td>
    <td>Local filename (full). Local filename can be different than capturefilename if download small or large thumbnails</td>
    <td>DSC_0014.NEF</td>
  </tr>
  <tr>
    <td>@filename_root@</td>
    <td>Local filename (root, without extension)</td>
    <td>DSC_0014</td>
  </tr>
  <tr>
    <td>@filename_ext@</td>
    <td>Local filename (extension)</td>
    <td>NEF</td>
  </tr>
  <tr>
    <td>@capturefilename@</td>
    <td>Capture filename (full)</td>
    <td>DSC_0014.NEF</td>
  </tr>
  <tr>
    <td>@capturefilename_root@</td>
    <td>Capture filename (root, without extension)</td>
    <td>DSC_0014</td>
  </tr>
  <tr>
    <td>@capturefilename_ext@</td>
    <td>Capture filename (extension)</td>
    <td>NEF</td>
  </tr>
  <tr>
    <td>@camerafolder@</td>
    <td>Camera folder of filename</td>
    <td>100D7200</td>
  </tr>
  <tr>
    <td>@slotnumber@</td>
    <td>Media card slot # file downloaded from (1 or 2)</td>
    <td>1</td>
  </tr>
  <tr>
    <td colspan="3" align="center"><strong>Camera Make/Model/Serial Specifiers</strong></td>
  </tr>
  <tr>
    <td>@cameramake@</td>
    <td>Camera Make</td>
    <td>Nikon</td>
  </tr>
  <tr>
    <td>@cameramodel@</td>
    <td>Camera Model</td>
    <td>D7200</td>
  </tr>
  <tr>
    <td>@cameraserial@</td>
    <td>Camera Serial Number</td>
    <td>35551323</td>
  </tr>
  <tr>
    <td colspan="3" align="center"><strong>Download File Number Specifiers</strong></td>
  </tr>
  <tr>
    <td>@dlnum@</td>
    <td>The nth file downloaded this Airmtp session (1..number of files downloaded)</td>
    <td>0045</td>
  </tr>
  <tr>
    <td>@dlnum_lifetime@</td>
    <td>The nth file downloaded for this camera model+serial for lifetime of Airmtp</td>
    <td>5345</td>
  </tr>
  <tr>
    <td colspan="3" align="center"><strong>Meta Specifiers</strong></td>
  </tr>
  <tr>
    <td>@replace~xxx~yyy@</td>
    <td>Replace every occurence of 'xxx' with 'yyy' for output string generated up to this point</td>
    <td>@replace~NEF~Raws@ converts &quot;NEF&quot; to &quot;Raws&quot;</td>
  </tr>
  <tr>
    <td>@replacere~xxx~yyy@</td>
    <td>Regular Express version of @replace. This uses the Python <a href="https://docs.python.org/2/library/re.html#re.sub" target="new">re.sub()</a> function. Python regex reference <a href="https://docs.python.org/2/library/re.html" target="new">here</a>.</td>
    <td>&nbsp;</td>
  </tr>
  <tr>
    <td>@@</td>
    <td>Literal '@'</td>
    <td>@</td>
  </tr>
</table>

When both --dirnamespec and --filenamespec are specified, --dirnamespec
is processed first. The output of --dirnamespec is then available as the
updated @path@ for --filename spec. For example, if you use "--outputdir
c:\\pics --dirnamespec @cameramake@ --filenamespec whatever" with a
Nikon camera, when --dirnamespec is processed the @path@ specifier
translates to c:\\pics. When --filenamespec is processed the @path@
specifier translates to c:\\pics\\Nikon

All specifiers except @replace@ can include optional subscripts to
select a subset of characters from the generated specifier string. The
first subscript is the starting character position. The second subscript
is the ending character position (exclusive). An empty first subscript
implies from the beginning of the string. An empty second subscript
implies to the end of the string. Subscript values can be negative,
which count from the end of the string.

Here are some examples based on a sample filename of DSC\_0014.NEF:

<table width="49%" border="1" cellspacing="0">
  <tr>
    <td width="20%"><strong>Example</strong></td>
    <td width="58%"><strong>What it Does</strong></td>
    <td width="22%"><strong>Output</strong></td>
  </tr>
  <tr>
    <td>@filename:4:8@</td>
    <td>Extract characters 4 through 7</td>
    <td>0014</td>
  </tr>
  <tr>
    <td>@filename::3@</td>
    <td>Extract characters from beginning through 2</td>
    <td>DSC</td>
  </tr>
  <tr>
    <td>@filename:4:@</td>
    <td>Extract characters 4 through end</td>
    <td>0014.NEF</td>
  </tr>
  <tr>
    <td>@filename:-3:@</td>
    <td>Extract last three characters</td>
    <td>NEF</td>
  </tr>
  <tr>
    <td>@filename:-3:-2@</td>
    <td>Extract one character starting 3 from the end</td>
    <td>N</td>
  </tr>
</table>

The case of any specifier's output can be changed via the options field.
The only exceptions are the @replace@ specifiers which uses the entire
entered case. The options field is after the two subscript fields - if
no subscripts are required than use three ':' as placeholders to skip
past them. Here are the available options:

<table width="49%" border="1" cellspacing="0">
  <tr>
    <td width="13%"><strong>Option</strong></td>
    <td width="87%"><strong>What it Does</strong></td>
  </tr>
  <tr>
    <td>u</td>
    <td>Entire specifier output is uppercased</td>
  </tr>
  <tr>
    <td>l</td>
    <td>Entire specifier output is lowercased</td>
  </tr>
  <tr>
    <td>c</td>
    <td>First character of specifier output is capitalized</td>
  </tr>
</table>

Here are some case examples based on a camera make of "Nikon":

<table width="49%" border="1" cellspacing="0">
  <tr>
    <td width="20%"><strong>Example</strong></td>
    <td width="58%"><strong>What it Does</strong></td>
    <td width="22%"><strong>Output</strong></td>
  </tr>
  <tr>
    <td>@cameramake:::u@</td>
    <td>Entire specifier output is uppercase</td>
    <td>NIKON</td>
  </tr>
  <tr>
    <td>@cameramake:::l@</td>
    <td>Entire specifier output is lowercase</td>
    <td>nikon</td>
  </tr>
  <tr>
    <td>@cameramake:::c@</td>
    <td>First character of specifier output is capitalized</td>
    <td>Nikon</td>
  </tr>
</table>

The @replace@ specifier is very powerful and allows you to perform
search/replacement operations. It is performed on the generated output
string at the point where the @replace@ occurs. This means it is
performed after any other specifier replacements up to that point. Here
are examples:\

<table width="98%" border="1" cellspacing="0">
  <tr>
    <td width="55%"><strong>Example</strong></td>
    <td width="22%"><strong>Sample Input</strong></td>
    <td width="23%"><strong>Output</strong></td>
  </tr>
  <tr>
    <td><p>--filenamespec @cameraserial@@replace~35551323~Main Camera@_@dlnum@@filename_ext@</p></td>
    <td>Serial #35551323,  DSC_0014.NEF</td>
    <td>&quot;Main Camera_0001.NEF&quot;</td>
  </tr>
  <tr>
    <td><p>--dirnamespec @cameramodel@\@filename_ext@@replace~NEF~Raw Files@</p></td>
    <td>D7200 and DSC_0014.NEF</td>
    <td>&quot;D7200\Raw Files&quot; (output directory)</td>
  </tr>
  </table>


The directory name generated by --dirnamespec is relative to --outputdir
(if specified) and can can include multiple directories - airmtpcmd will
recurse to generate the necessary tree of subdirectories for any
directory that doesn't already exist within the path. For example,
--outputdir c:\\mypics --dirnamespec
"@cameramodel@\\@cameramake@\\@cameraserial@" will create (if necessary)
the directories c:\\mypics\\Nikon, c:\\mypics\\Nikon\\D7200, and
c:\\mypics\\Nikon\\D7200\\35551323. After processing --dirnamespec the
resulting directory name/path is converted to an absolute path.

**--downloadexec** executable\_specarg \[specargs ...\] (added in v1.1)\
Launches an application/script for each file downloaded. 'executable' is
the name of the app/script. 'specargs' is one or more arguments to pass
to the launched application/script, using the same spec renaming
mechanism provided by --dirnamespec/--filenamespec. At a minimum you'll
likely need to pass the name of the downloaded file to your app/script,
which you can do via --downloadexec myappname @pf@. Note that the @path@
specifier will refer to the generated path if you included a
--dirnamespec, or absent that the output path if you specified
--outputdir. The @filename@ specifier refer to the generated filename if
you included a --filenamespec, plus a potential "--new-x" suffix to the
root name if there was a file in the output directory with the same name
as the generated filename (if --ifexists is set to uniquename). If no
--filenamespec was specified then @filename@ will refer to the capture
filename stored on the camera, again with a potential "--new-x" suffix
if the file had to be renamed due to a name conflict with an existing
file in the output directory. Be careful when using this option with
applications that aren't single-instanced, ie they start a new instance
every time they're invoked. This can cause a large amount of application
windows to be opened depending on how many files you're downloading. If
the specifier result of the first argument results in an empty string
then launching for that file will be skipped. You can specify different
executables for various file types via use of the @replace@ specifier,
for example: --downloadexec
"@filename\_ext@@replace\~JPG\~myappforjpgs.exe@@replace\~NEF\~myappfornefs.exe@"
@pf@. By default all file types will invoke the downloadexec
specification; use --downloadexec\_extlist to limit by file extension.
You can set additional exec options via --downloadexec\_options.

To pass arguments that require a leading '-' or '--' prefix use '\~' or
'\~\~' instead. By default airmtpcmd will convert the tilde characters
of specarg into dashes after processing the secparg string(s) \[it will
not do this replacement on executable\_specarg, to allow the use of
tildes for the executable path/name\]. Using tildes is required because
any leading '-' or '--' prefix will be interpreted by airmtpcmd as an
argument to itself rather than an argument to pass to your launched
application. If you need to use literal tildes in your argument string
then you can disable this default replacement behavior by using
--downloadexec\_options notildereplacement. You you can then use a
manual replacement specifier to support passing arguments that require a
leading '-' or '--'. For example you can use --downloadexec\_options
notildereplacement --downloadexec myapp.exe
++single-window@replace\~++\~--@ to execute "myapp.exe --single-window".

Each specarg is processed separately. This means @replace@ specifiers
operate on that spec string only. For example, --downloadexec myapp.exe
OPEN OPEN@replace\~OPEN\~CLOSE@ will result in myapp.exe OPEN CLOSE. You
can enclose a specarg in quotes if you want it processed as a single
string but it will be passed to the launched application as a single
argument so any attempt to embed multiple arguments in a single quoted
specarg string will likely not produce the results you want (ie, the
launched program will interpret the multiple arguments of the single
specarg as a single argument, likely resulting in it reporting that the
argument name is not recognized).

**--downloadexec\_extlist** \[extension ...\]\
Specifies which types of files (by extension) that an optional
--downloadexec will be performed on. By default all file types will be
launched for --downloadexec.

**--downloadexec\_options** \[options ...\] (added in v1.1)\
Various options for handling the result/timing of the application/script
launched --downloadexec. 'ignorelauncherror' will ignore any failure to
launch the executable (such as the executable not being found). 'wait'
will wait for the launched app to complete before proceeding to the next
download. 'exitonfailcode' will exit if the launched application returns
a non-zero exit status (must include 'wait' option for this to work,
otherwise return code of launched application can't be checked). 'delay'
will delay for 5 seconds after launching application before proceeding
to the next download. 'notildereplacement' will disable the default
behavior of replacing tilde characters with dashes.

**--realtimepollsecs seconds** (added in v1.1)\
The interval at which airmtp will poll the camera for new images in
realtime download mode. The default is every 3 seconds. Use a longer
interval to help increase camera battery life, or a shorter interval for
faster download response times. Setting the interval too high may cause
session timeouts because some cameras will consider the connection lost
after extended periods of no communication from airmtp. For example
Nikon cameras will drop a session after about 30 seconds of inactivity.

**--logginglevel** \[normal | verbose | debug\]\
The verbosity level of logging for an airmtpcmd session. Airmtp outputs
its messages both to the console (stdout/stderr) and to a pair of
logging files, named airmtpcmd-log-last.txt (log messages from most
recent session) and airmtpcmd-log-lifetime.txt (log messages from all
sessions). 'normal' indicates that only important/useful informational
messages will be logged. These include messages such as the connected
model/serial number of the camera and information about each file
downloaded/listed. 'verbose' includes some additional messages, useful
for instance when you'd like more information about why a particular
file was not downloaded. 'debug' will include all developer-level
messages and debug information, including hex dumps of all MTP-IP
communication between the airmtpcmd and the camera. The default logging
level is 'normal'.

**Debug/Troubleshooting arguments:**

The following is a list of less common arguments that can be used when
troubleshooting or debugging the operation of airmtpcmd. These options
are hidden from the --help display, to limit the clutter of options
presented for normal use.

**--connecttimeout** &lt;seconds&gt;\
The amount of time to wait for a TCP/IP socket connection to be
established with the camera. The default is 10 seconds. When Nikon's ad
hoc wireless network is ready the camera usually connects very quickly.
However it may take a little longer if the user just enabled the WiFi
option on the camera and/or just selected the network on his computer.
Canon bodies usually take a bit longer to establish a connection, esp if
its WiFi has been idle for some period of time.

**--socketreadwritetimeout** &lt;seconds&gt;\
The amount of time to wait for a single TCP/IP socket read/write request
to complete. The default is 5 seconds.

**--retrycount** &lt;number&gt;\
The number of full-cycle retries airmtpcmd will perform before
completing its configured action on all files. By "full-cycle" I mean
the process of recovering from a failed transaction, which includes
restarting the full MTP-IP session. The default is unlimited.

**--retrydelaysecs** &lt;number&gt;\
The number of seconds to pause between full-cycle retries. The default
is 5 seconds. This value was chosen to allow some measure of time for
the camera to reestablish its ad hoc wireless network; typically the
camera will require a few retry cycles before it is ready for a new
MTP-IP session after a failed attempt.

**--printstackframes** \[no | yes\]\
Print stack frames for all exceptions. The default is to only print
stack frames for programming exceptions, such as AssertionError,
ValueError, etc..

**---mtpobjcache** \[enabled | writeonly | readonly | verify |
disabled\]\
Controls the behavior of the MTP object info cache. Every file on the
camera is represented by an MTP object that describes its attributes
such as filename, date, size, type, etc.. Airmtp retrieves the full list
of object infos at the start of execution - this list is required to
support the criteria filtering and date sorting features of the program.
Some cameras take a long time to complete many MTP\_OP\_GetObjectInfo
requests, accessing the media card for each request on-demand rather
than using predictive read-ahead caching to anticipate the next
MTP\_OP\_GetObjectInfo request. This can make repeated executions of
airmtpcmd slow. To avoid incurring this penalty for every invocation,
airmtpcmd caches the last list of object infos it obtained on a per
model/serial number basis, storing the cache as a file in its local
appdata directory. The default of 'enabled' enables the MTP object
cache. The cache has mechanisms to ensure both the integrity and
coherency of the cache, the latter of which requires algorithms to avoid
cases where the cached copy of object infos can become stale relative to
what's on the camera. The following options are used to verify and
troubleshoot these mechanisms. 'writeonly' disables cache hits for this
invocation but still enables writing the persistent cache file.
'readonly' enables cache hits for this invocation but disables updating
th persistent cache file. 'verify' is the same as 'enabled' but will do
a full coherency check of the cache - this involves performing a
MTP\_OP\_GetObjectInfo for each object on the camera and verifying any
cached copy against that information. 'disabled' will turn off the cache
completely for this invocation.

**---mtpobjcache\_maxagemins** \[minutes\]\
The MTP object info cache includes a timestamp of when it was last
updated. This options controls how old the cache is allowed to be (ie,
relative to its last update) before it is fully invalidated. The default
is zero, which means no age limit. Any other value is an age limit in
minutes.

**---maxgetobjtransfersizekb** \[kilobytes\]\
The maximize request size for MTP\_OP\_GetPartialObject requests in
kilobytes, which is the MTP request used to retrieve the full-size
image/movie files. During Airmtp development it was discovered that
Nikon's MTP-IP implementation has a bug in its processing of
MTP\_OP\_GetObject requests that cause transfers to get progressively
slower and eventually lead to a complete halt of transfers, requiring
the MTP session to be restarted to recover. It appears Nikon's firmware
is committing internal memory for the entire object and eventually runs
out of memory. The solution is to use MTP\_OP\_GetPartialObject, which
allows the transfer of an object in separate segments rather than the
full object as is done with MTP\_OP\_GetObject. This option sets the
maximum size we request for each segment. The default is 1024 (1MB),
which was empirically determined to be large enough to saturate Nikon's
WiFi interface throughput while being small enough to avoid any memory
issues in the camera. The actual request size may be further constrained
by the --maxgetobjbuffersize parameter; for example, if the max transfer
size is 1MB but the max buffer size is 256KB, the size of each
MTP\_OP\_GetPartialObject transfer will be the smaller of the two, in
this case 256KB. This parameter has no effect for --action
getlargethumbs and --action getsmallthumbs since the MTP interface
requires those to be obtained via MTP\_OP\_GetObject - those elements
are typically very small and thus aren't sensitive to the Nikon issue
related to large transfers.

**---maxgetobjbuffersizekb** \[kilobytes\]\
The maximum number of kilobytes we buffer across
MTP\_OP\_GetPartialObject requests for a full-size image/movie file
download before we flush the data. The default is 32768 (32MB). The
value should be large enough to maximize throughput on the filesystem
(although in most cases filesystem caches will ensure this through write
caching) but small enough to limit airmtpcmd's memory footprint.

**--initcmdreq\_guid** \[16-byte hex guid in two 8-byte hex double-words
| mac address\] (added in v1.1)\
Specifies the 16-byte host GUID that airmtp presents to the camera
during MTP\_TCPIP\_REQ\_INIT\_CMD\_REQ, which is the first request sent
to the camera. This option is used for debugging support on new camera
models that may require specific GUID values. The format is either a
hi-low pair of hex values (example: --initcmdreq\_guid
0x7766554433221100-0xffeeddccbbaa9988) or a six-field hex MAC address
(example --initcmdreq\_guid 43:56:22:98:35:32). For the 16-byte hex
option the bytes are ordered such that the hi-field (first hex value) is
sent first, in presumed big-endian GUID word order, with the order of
individual bytes being little endian on little-endian platforms (for
example --initcmdreq\_guid 0x7766554433221100-0xffeeddccbbaa9988 will be
go out on the wire as 00 11 22 33 44 55 66 77 88 99 aa bb cc dd ee ff).
The six-field hex MAC address is to support Sony's exclusive host
feature when desired, where the camera will only accept the GUID if its
lower six bytes match the MAC address for which the camera is
authenticated for using Sony's PlayMemories Home (Windows) or Auto
Import App (OSX) \[the lower six bytes of the GUID are the mac address,
with bytes 7-8 as 0xFF). The default GUID for airmtp v1.0 was
0x7766554433221100-0xffeeddccbbaa9988 (matching the GUID Nikon's WMU app
presents to cameras), but was changed in v1.1 to
0x7766554433221100-0x0000000000009988 to support Sony cameras, who will
only accept a non-MAC address matching GUID if the last six bytes of the
GUID are zero, corresponding to what Sony interprets as the MAC address
of the host.

**--initcmdreq\_hostname** \[hostname\] (added in v1.1)\
Specifies the host name string that airmtp presents to the camera during
MTP\_TCPIP\_REQ\_INIT\_CMD\_REQ, which is the first request sent to the
camera. This option is used for debugging support on new camera models
that may require specific hostname values. The default is 'airmtp'.

**--initcmdreq\_hostver** \[4-byte hex word\] (added in v1.1)\
Specifies the host version that airmtp presents to the camera during
MTP\_TCPIP\_REQ\_INIT\_CMD\_REQ, which is the first request sent to the
camera. This option is used for debugging support on new camera models
that may require a specific host version value. The default is
0x00010000, which is interpreted by MTP-IP as 1.00

**--opensessionid** \[4-byte hex word\] (added in v1.1)\
Specifies the session ID that airmtp uses for the MTP\_OP\_OpenSession
request, which is the command that starts a high-level MTP session with
the camera. This option is used for debugging support on new camera
models that may require a specific session ID value - by default airmtp
uses the session ID by the camera in response to a
MTP\_TCPIP\_REQ\_INIT\_CMD\_REQ. However some newer Nikon cameras like
the J5 and P900 expect a hard-coded session ID of 0x00000001 - to
support these models airmtp will first attempt the session ID returned
by MTP\_TCPIP\_REQ\_INIT\_CMD\_REQ; if that fails airmtp will then retry
the MTP\_OP\_OpenSession with a hard-coded session ID of 0x00000001.

**--maxclockdeltabeforesync** \[seconds | disablesync | alwayssync\]
(added in v1.1)\
Specifies the maximum clock delta allowed (in seconds) between the
camera and system before airmtp will send an MTP command to the camera
to synchronize its time to the computer system airmtp is running on.
This check is performed once per airmtp session. Synchronization the
camera's date/time is currently only supported on Nikon and Canon
bodies. For Canon bodies value of 'seconds' is ignored - the clock is
always synchronized provided 'disablesync' is not specified. The default
is 5 (seconds). 'disablesync' disables the clock synchronization
feature. 'alwayssync' will always set the cameras clock, irrespective of
whether it's out of sync with the system's clock.

**--camerasleepwhendone** \[yes | no\] (added in v1.1)\
Specifies whether the camera is put into sleep mode at the end of an
airmtp session (ie, low power mode where the camera may still be on but
requires a button press to wakeup) . The default is yes. The only camera
that presently supports this is Sony. This command is important for Sony
cameras because if the camera is not put to sleep then it will remain in
the 'Send to Computer' mode even after the airmtp session completes.
Sony appears to only support one MTP session per TCP/IP socket
connection - when a session ends the camera will remain in 'Send to
Computer' mode (even if a command is sent to change the message and make
it appear its no longer in that mode, such as the "saving process
canceled message") - any attempt at a subsequent MTP session will result
in the camera accepting a new TCP/IP socket connection but not
responding to any MTP commands, making it appear to the user that the
WiFi is no longer working. The only way to recover from this is to press
'Cancel' on the 'Send to Computer' screen and then perform another 'Send
to Computer' operation. The alternative used by airmtp is to put the
camera to sleep after the session, which is the only way I've found so
far that is guaranteed to get the camera out of the initial 'Send to
Computer' mode. If you set this option to 'no' then airmtpcmd will log a
warning message at the end of very session indicating that the user must
press 'Cancel' on the 'Send to Computer' screen before attempting a new
airmtp session with the camera.

**--sonyuniquecmdsenable** \[4-byte hex word with bitmask flag values\]
(added in v1.1)\
Specifies which Sony-proprietary commands should be issued to Sony
cameras during airmtp operation. These commands are undocumented and
were reverse-engineered during v1.1 development. It doesn't appear that
any of the commands are required for normal MTP functioning but the
option to send them is being provided in case certain Sony camera models
are found to require them. The default value is 0x00000001, to enable
the command that displays "Sending... on the 'Send to Computer' screen
of the camera. The bitmask values for this field are:

> SONY\_UNQIUECMD\_ENABLE\_SENDING\_MSG = 0x00000001\
> SONY\_UNQIUECMD\_ENABLE\_UNKNOWN\_CMD\_1 = 0x00000002\
> SONY\_UNQIUECMD\_ENABLE\_SAVING\_PROCESS\_CANCELLED\_MSG = 0x00000004

**--suppressdupconnecterrmsgs** \[yes | no\] (added in v1.1)\
v1.1 added the automatic suppression of redundant connection-failure
messages when it performs retries of connection attempts. These message
include timeout/not-responding messages. This was added to prevent a
constant stream of messages while airmtpcmd is waiting for the camera to
become available to connect, particularly for the new --realtimedownload
mode where some workflows may involve the user intentionally turning
WiFi off/on while shooting as a means to control when the camera sends
realtime images to airmtp. The default is yes.

**--rtd\_pollingmethod** \[integer value corresponding to a
REALTIME\_DOWNLOAD\_METHOD\_\* constant\] (added in v1.1)\
"rtd" prefix is short for "realtimedownload". Specifies the polling
method used for detecting when the camera might have new images to
download. The default is to determine the method by the camera make. A
value of 0 is the Nikon-specific event mechanism. A value of 1 is the
generic MTP polling method. A value of 2 is to exit the session and wait
for the camera to become available again (for cameras that don't allow
operation while in WiFi mode, such as all current Sony cameras).

**--rtd\_mtppollingmethod\_newobjdetection** \[objllist | numobjs\]
(added in v1.1)\
"rtd" prefix is short for "realtimedownload". Specifies the method used
for detecting new objects on the camera when using the MTP polling
method, which is the generic method used on cameras for which airmtp
doesn't support the camera's native event mechanism. Presently airmtp
only supports the Nikon event mechanism, so it uses the MTP polling
method for Canon. The MTP polling method has two algorithms for
detecting the possibility of new images in the camera - it can either
check for a change in the object handle list or a change in the number
of objects, the latter of which then requires retrieving the object
handle list to establish which handles are new. The numobjs method would
seem to be more efficient since it requires only retrieving a single
32-bit value from the camera - however the problem with this method is
that there's a timing hole if the user deletes an image in-camera and
then takes a new one in between one of our polling intervals - the
object count will be the same and we'll fail to detect a new image (-1
for deleted image, +1 for new image). For this reason the default
algorithm is objlist, which actually was found to execute faster on a
Canon 6D than the object count algorithm. I left the numobjs algorithm
in the code in case there is a camera model where the objlist method
runs very slow.

**--rtd\_maxsecsbeforeforceinitialobjlistget** \[seconds\] (added in
v1.1)\
When --realtimedownload is set to 'only' Airmtp can avoid the
time-consuming retrieval of the initial list of objects/files from the
camera. This is because it's configured to only capture images taken
after Airmtp has launched and thus doesn't need to evaluate the
timestamps of existing images on the camera against any capture date
criteria. However Airmtp must also consider the scenario of the user
starting Airmtp in realtime-only mode but with the camera initially
unavailable for a connection, such as if he powers his camera
on/WiFi-enable after launching Airmtp or if he's using a workflow of
taking photos offline and then periodically enabling WiFi to transfer
after evaluating/deleting images in the camera he doesn't want. For this
reason Airmtp places a tight time constraint on how long it allows the
initial connection to the camera to take before it considers the risk of
missing images too great (ie, images taken by the user after launching
Airmtp but before making the camera available for WiFi connection -
these images will be overlooked by Airmtp if it doesn't download the
initial list of objects/files from the camera and evaluate their
timestamps against the Airmtp launch time to establish which images are
to be considered 'realtime' and downloaded). This parameter controls
this constraint and defaults to 5 seconds - if the the initial
connection to the camera takes any longer than the configured interval
then Airmtp will perform the initial retrieval of file/object info from
the camera even in realtime-only mode. This parameter is being made
available in case there are cameras that take longer than 10 seconds for
the initial connection and the user wants the performance/response-time
benefit of skipping the retrieval of the initial list of objects/files
from the camera. Any photos taken in the interval of this configured
parameter will not be downloaded so it's use is limited to scenarios
where the user will wait for Airmtp to establish its initial connection
before the user takes any photos.

**--ssdp\_discoveryattempts** \[value\] (added in v1.1)\
Specifies the number of times the SSDP logic will multicast an SSDP
M-SEARCH message on the network interface(s). Each discovery attempt
involves the transmission of an M-SEARCH message followed by a wait for
'x' seconds for a response from devices, where 'x' is configured via
--ssdp\_discoverytimeoutsecsperattempt. The default attempts value is 3.

**--ssdp\_discoverytimeoutsecsperattempt** \[seconds\] (added in v1.1)\
The amount of time the SSDP logic will wait for a response for each
M-SEARCH message sent. The default is 2 seconds.

**--ssdp\_discoveryflags** \[4-byte hex word with bitmask flag values\]
(added in v1.1)\
Various flags to control the operation of the SSDP logic. See ssdp.py
for details on each flag

> SSDP\_DISCOVERF\_CREATE\_EXTRA\_SOCKET\_FOR\_HOSTNAME\_IF =
> 0x00000001\
> SSDP\_DISCOVERF\_USE\_TTL\_31 = 0x00000002\
> SSDP\_DISCOVERF\_ENABLE\_MULTICAST\_RX\_ON\_PRIMARY\_SOCKET =
> 0x00000100\
> SSDP\_DISCOVERF\_ENABLE\_MULTICAST\_RX\_ON\_HOSTNAME\_IF\_SOCKET =
> 0x00000200\
> SSDP\_DISCOVERF\_ENABLE\_MULTICAST\_RX\_ON\_ADDITIONAL\_SOCKETS =
> 0x00000400

--**ssdp\_addmulticastif** \[IP address of interface ...\] (added in
v1.1)\
Adds interface(s) to list of interfaces that the SSDP discovery logic
will transmit M-SEARCH messages and listen for responses on. By default
the SSDP logic will create a single TCP/IP socket for its broadcasts,
specifying INADDR\_ANY so that the system will select the default
network interface. On Windows an additional socket is also used for the
local host name, to work around
an[issue](https://social.msdn.microsoft.com/Forums/windowsdesktop/en-US/36abbd31-1882-49c3-999e-5cf8d4bfe9c5/upnp-discovery-failures-caused-by-windows-ssdp-discovery-service-changing-default-multicast?forum=windowsgeneraldevelopmentissues)
I found with the Windows SSDP discovery service. This parameter allows
you to add additional interfaces (by IP address) on which the SSDP logic
should send and listen for SSDP broadcasts \[creates an additional
socket for each interface, specifying the interface's IP address as the
multicast interface\]. This parameter is useful in systems with multiple
network adapters and the camera is on an adapter other than the system
default interface.

--**ssdp\_addservice** \[UPnP service name\] (added in v1.1)\
Adds an additional UPnP service identifier that the SSDP discovery logic
uses for its M-SEARCH multicasts/listens. Every camera manufacturer has
a unique UPnP service identifier for their cameras. Airmtp currently
knows of two identifiers - one for Sony and Canon. Use this option to
add support for an additional manufacturer, or if the identifier changes
for an existing support manufacturer. The two built-in identifiers are
"urn:microsoft-com:service:MtpNullService:1" (Sony cameras) and
"urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1" (Canon
Cameras).

## Articles about Airmtp

[Thom Hogan - Finally, Desktop WiFi](http://www.dslrbodies.com/accessories/software-for-nikon-dslrs/software-news/finally-desktop-wifi.html)

[DPReview - Airmtp brings desktop Wi-Fi transfer to Nikon users](https://www.dpreview.com/articles/6089807566/airmtp-brings-desktop-wi-fi-transfer-to-nikon-users)

## Features Planned for Next Release

 * A fully self-contained GUI app with visual selection of images to download
 * Potential support for DslrDashboardServer

## Developer Notes

For anyone interested in the ongoing progress of Airmtp development, there is a [developer notes](http://www.testcams.com/airnef/developer/) page.

## GPL v3 License

    airmtp - Wirelessly download images and movies from your Nikon Camera
    Copyright (C) 2015, testcams.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Credits

-   This is based on [airnef](http://www.testcams.com/airnef/) by [testcams.com](http://www.testcams.com/). Many thanks to the comprehensive work done there!
-   Special thanks to Joe FitzPatrick [for his work on
    reverse-engineering Nikon's WiFi
    interface](https://nikonhacker.com/wiki/WU-1a)
-   Camera bitmap courtesy of
    ['rg1024](https://openclipart.org/detail/20364/cartoon-camera)'
-   Computer bitmap courtesy of
    '[lnasto](https://openclipart.org/detail/171010/computer-client)'
-   WiFi icons/bitmaps courtesy of
    '[neorg](https://openclipart.org/detail/191831/wifi-icon)' and
    '[MrTossum](https://openclipart.org/detail/166617/wireless)'
-   Camera Icon courtesy of
    '[Paomedia](https://www.iconfinder.com/icons/285680/camera_icon)',
    licensed under Creative Commons (Attribution 3.0 Unported)

