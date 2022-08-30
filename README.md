# slack-backup

This Python script downloads a backup of all Slack users, all channels
(*including private channels*), and all messages in those channels.
The produced dump is in the same format produced by an
[official Slack export of workspace data](https://slack.com/help/articles/201658943-Export-your-workspace-data)
(which works well for public channels but not private channels).

The intended use-case for moving old Slack content over to a new
Discord server via
[slack-to-discord](https://github.com/pR0Ps/slack-to-discord)
(tested) or
[Slackord2](https://github.com/thomasloupe/Slackord2) (untested).
One motivation is Slack's
[change in limits to the free plan](https://slack.com/help/articles/7050776459923-Pricing-changes-for-the-Pro-plan-and-updates-to-the-Free-plan).

## Usage

### Running slack-backup

1. Clone this repository.
2. Install Python 3 if needed.
3. `pip install slack_sdk`
4. [Create a Slack app](https://api.slack.com/apps/new)
5. Under OAuth &amp; Permissions, in the User Token Scopes section
   (I've found the user token to work better than the bot token, but YMMV),
   add the following scopes:

   * `admin` (not sure whether this is necessary)
   * `channels:history`
   * `channels:read`
   * `groups:history`
   * `groups:read`
   * `users:read`
   * `users:read.email`

   Also write down the Bot User OAuth Token.
   (These directions are based on
   [this documentation](https://github.com/docmarionum1/slack-archive-bot).)
6. I recommend also running an
   [official Slack export of workspace data](https://slack.com/help/articles/201658943-Export-your-workspace-data).
   In JSON files containing file uploads you'll URLs ending with
   `?t=xoxe-...`.  Write down that token too.
7. Then I suggest creating a `run` script with the following contents:

   ```sh
   #!/bin/sh
   export TOKEN='xoxp-...'  # Bot User OAuth Token
   export FILE_TOKEN='xoxe-...'  # file access export token from previous step
   python slack_backup.py
   ```
8. Run the `run` script via `./run` and wait.
9. The output will be in a created `backup` subdirectory.
10. To produce a `backup.zip` file in the same format as a Slack export,
    do the following in a shell (assuming you have `zip` installed):

    ```sh
    cd backup
    zip -9r ../backup.zip *
    ```
