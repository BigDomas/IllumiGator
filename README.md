# IllumiGator
2D Light-Based Puzzle Game

## Source Code and Other Resources
[GitHub](https://github.com/BigDomas/IllumiGator)

[Miscellaneous](https://drive.google.com/drive/folders/1HQ1lIxgZJNANgWnts3bsWUUTnnfJrKXW?usp=sharing)

## Dependencies
arcade
numpy
screeninfo

## Install
pip install illumigator

run **illumigator** command

## Create Levels
- First create or download an appropriately formatted JSON file containing your level.
- Move the file into the _illumigator/data/levels/community_ directory.
- If you are adding it while in the level selection menu, press R to refresh the page.
- That's it!

INTERFACE
--
 - Element Visibility: We utilize distinct, contrasting colors and clear geometric shapes for the different elements. The player character, enemy bot, obstacles, and moveable objects are all clearly defined and uniquely designed so that they are distinguishable. When a player is within the required range to manipulate an interactable object, the object is highlighted with a blinking red outline to make it more visible to the user.
 - Element Usability: Controls for the player character include movement and interaction. They are clearly mapped to intuitive keys (arrow keys and WASD for movement and Q and E for object rotation) to allow for straightforward user gameplay. The controls can also be found within the controls menu option.
Intuitiveness: The game design is simple and intuitive. The player character moves in the direction for the key presses, and the red highlight makes it clear when a mirror object can be rotated. The object physics work as they do in the real-world, so with a basic understanding of reflection and refraction, the user should be able to solve the puzzles. Even without much of an understanding of these topics, this is an opportunity for the player to learn how these physics work with the easy-to-understand visuals.
 - Consistency: The same keys are used consistently to control the player throughout the game, and the visual style remains consistent across different levels and game states. The physics are consistent with those found in the real-world, and stay that way throughout each level.
 - Status Visibility: Since the player character can be killed with one collision with the enemy bot, there are no status indicators for health. However, the character has an idle animation when not moved for a certain amount of time, running animations for when the movement keys are pressed, and a death animation for when the enemy collides with the player. The enemy has the states asleep and aggro, which are indicated by its sprites and animation. When asleep, there is a sleeping animation that clearly depicts this. When the user directs the light rays towards it, it triggers the awake state, which is indicated by a running animation. 

NAVIGATION
--
 - Mechanics / API: The game mechanics are fairly self-explanatory, with the only controls being player movement and rotation. It is expected that there will be some trial and error for the puzzles with each level, but the visuals allow for the users to discover how each element of the game works easily, with each element having consistent functionality in each level.
 - Tested / Not Buggy: Movement was thoroughly tested. Movement speed is normalized (meaning player movement with two keys is the same as one). We also implemented collisions with all of the world objects so that players can’t go through objects. Finally, animations were added in order to improve user experience.
 - Minimal Acclimation: The game uses common control schemes for player movement and for the object interactions, the controls are simple and explained in the control menu. The game mechanics are simple and intuitive, allowing the user to quickly understand how to navigate the game world.
Predictability: The movements of both the player character and the enemy bot are predictable based on the user’s inputs and the defined AI behaviors. As for the physics of the game, formulas used to calculate reflection and refraction in the real-world were used for the game objects, thus allowing for an intuitive experience based on real-world experience.
 - Discoverability: The game encourages exploration and experimentation, with the user learning how to navigate and interact with the game world through playing. While the level and sprite designs are intuitive, the puzzles can still be challenging to solve and some of the mechanics will be trial and error, with each user learning at their own pace. Users can upload their own custom levels as well, which allows for people to upload their own creative level designs based on how they perceive the game.

USER PERCEPTION
--
 - Enjoyability: This game is targeted towards people who enjoy or would like to learn more about light physics as well as those who enjoy puzzle games. It is very fun and awesome 😀
 - Minimal Frustration: UI is consistent and gameplay is intuitive. Players can easily navigate through menus with the same keys they use to navigate the character in game. 
 - General Usability: Design is intuitive and user friendly. Users can resize the game window to whatever resolution they desire. They can fullscreen the game. Finally they can adjust their audio settings to desired levels.

RESPONSIVENESS
--
 - Action Indications / Non-Blocking: The nearest interactable mirror is highlighted. The florida-man’s state is indicated by sleeping or awake with red eyes if aggravated. The state of the planet is also indicated by the color of the planet and explodes when fully charged.
 - State Indications: State is clearly indicated by UI. State change is consistent. Different menus appear for each of the game states, unless in the game state where users can play a level.
 - Task Success: Users successfully complete a level when they fully charge a planet. Upon fully charging a planet, it explodes. The user is then greeted with a win screen. The user has the ability to retry, quit to the menu, or continue to the next level (only if it isn’t the last official level).
 - Task Failure: A level can be failed by the user dying the florida-man, our hostile AI. Upon death users are greeted with a death screen and they can choose to retry or quit to the menu. Since the game is also a puzzle game, users can fail to solve the puzzle in a reasonable amount of time.

BUILD QUALITY 
--
 - Robustness: The game has no known bugs or crashes.
 - Consistency: Theming throughout the game is consistent throughout. Gameplay mechanics and visuals also remain consistent. Expected output from input remains consistent.
 - Aesthetic Rigor: We used different fonts, sounds, and custom sprites in order to achieve our aesthetic. The aesthetic of IllumiGator can be described as a futuristic space theme, where a gator destroys planets by redirecting a star’s rays.

FEATURES
--
 - Front-End: We used arcade, a library for creating 2D games to implement our front-end graphics. This includes our UI, graphics, and state updating to decide what to draw. 
 - Data Store: We save the store the user’s config on closing of the application. This allows settings of the user such as their current level and settings to be loaded in the future. We also store our levels in JSON format so that they can be created and imported by users. Rather than open each community level added, we use a metadata file and compare modification dates to find which files need to be updated.
 - Back-End: Implemented Illumiphysics. We have back-end physics scripts that calculate light intersections with different geometry. We optimize our back-end service using numpy vector calculations (since they are SIMD and C binded).


