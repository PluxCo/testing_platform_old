# Testing System

The **Testing System** is a project designed to assess individuals' knowledge of a specific topic. It comprises three
main components: a web panel, a Telegram bot, and a schedule module. This system allows you to evaluate how well
people grasp a particular subject by asking them questions through a conversational Telegram bot.

## Components

### 1. Admin Panel

The admin panel serves as the control center for managing the topic testing system. It provides an interface to:

- Add, edit, or delete questions related to the topic.
- Monitor user progress and scores.
- Configure system settings, such as the time intervals between questions.
- Assign and manage PIN for users to access the Telegram bot.

To access the admin panel, launch your web browser and navigate to the specified URL. You will need to log in using your
administrator credentials.

### 2. Telegram Bot

The Telegram bot acts as an interactive conversational agent that engages users in a topic-related conversation.
However, users can only access the bot if they possess a valid PIN, which is assigned through the admin panel. The bot
presents questions to users and maintains a dialogue-like experience. The bot aim is to create a natural and engaging
testing experience.

To interact with the bot, users need to initiate a conversation on Telegram, enter the provided PIN, and then start the
testing process. They can answer questions as prompted by the bot.

### 3. Schedule Module

The schedule module is responsible for generating a testing schedule for users. It calculates suitable times at which
users will be asked questions based on their availability and preferences. This ensures that users are engaged at times
convenient for them, enhancing their participation in the testing process.

## Usage

### Running the Project Locally

For debugging and testing purposes, you can run the project locally using the `main.py` file. Before running the file,
make sure you set the necessary environment variables. You can set these variables using the following commands:

```bash
export TGTOKEN=<telegram_token>
export ADMIN_PASSWD=<admin_password>
python main.py
```

Replace `<telegram_token>` with your actual Telegram bot token and `<admin_password>` with the desired administrator
password.

### Creating Docker Volume

Before running Docker Compose, you need to create a Docker volume for data persistence. Execute the following command:

```bash
docker volume create testing-data
```

### Running the Project with Docker Compose

To deploy the project in a production environment, Docker Compose is utilized. The following example Docker Compose
configuration can be used as a starting point:

```yaml
version: '3'
services:
  web:
    build: https://github.com/PluxCo/testing_platform.git
    volumes:
      - testing-data:/app/data
    ports:
      - "80:5000"
    environment:
      - TGTOKEN=<telegram_token>
      - ADMIN_PASSWD=<admin_password>
volumes:
  testing-data:
    external: true
```

Replace `<telegram_token>` with your actual Telegram bot token and `<admin_password>` with the desired administrator
password.

To run the project, navigate to the directory containing the `docker-compose.yml` file and execute the following
command:

```bash
docker compose up --pull always --build
```

This will start the project in detached mode, allowing it to run in the background.

## Getting Started

1. Clone or download the project repository.
2. Set up your Telegram bot by following
   the [Telegram Bot API documentation](https://core.telegram.org/bots#how-do-i-create-a-bot).
3. Configure the web admin panel settings as per your requirements.
4. Assign PIN to users via the admin panel for them to access the Telegram bot.
5. Customize the question database to suit the topic you wish to test.
6. Deploy the project using Docker Compose, ensuring you replace placeholders with actual values.

## License Agreement

---

This software and its associated documentation are proprietary and confidential. Unauthorized copying, transferring, or reproduction, in whole or in part, of the contents of this project, via any medium, is strictly prohibited.

**Usage Restrictions**

The receipt or possession of the source code and/or any parts thereof does not confer or imply any right to use them for any purpose other than the intended purpose for which they were provided.

**Redistribution and Modification**

Redistribution and use, with or without modification, are strictly forbidden without the explicit written permission of the project holders.

**Disclaimer of Warranty**

This software is provided by the copyright holders and contributors "as is" and without any express or implied warranties, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose.

**Limitation of Liability**

In no event shall the copyright holder or contributors be liable for any direct, indirect, incidental, special, exemplary, or consequential damages, including but not limited to procurement of substitute goods or services, loss of use, data, or profits, or business interruption, arising in any way out of the use of this software, even if advised of the possibility of such damage.

**Contact Information**

For licensing inquiries or permissions, please contact the project holders:

- Chernyshev Sergey: serg.miass340@gmail.com
- Chuvashov Anton: antonchuvashow@gmail.com
- Valik Elena: alenka.valik@ya.ru
- Zhilin Rostislav: clavic000@gmail.com

© 2023 Chernyshev Sergey, Chuvashov Anton, Valik Elena, Zhilin Rostislav. All rights reserved.
