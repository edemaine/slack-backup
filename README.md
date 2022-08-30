# slack-backup

This Python script downloads a backup of all Slack users, all channels
(*including private channels*), and all messages in those channels.
The produced dump is in the same format produced by an
[official Slack export of workspace data](https://slack.com/help/articles/201658943-Export-your-workspace-data)
(which works well for public channels but not private channels).

The intended use-case for moving old Slack content over to a new
Discord server via
[slack-to-discord](https://github.com/pR0Ps/slack-to-discord),
given Slack's
[change in limits to the free plan](https://slack.com/help/articles/7050776459923-Pricing-changes-for-the-Pro-plan-and-updates-to-the-Free-plan).
