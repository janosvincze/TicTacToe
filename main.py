#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
import datetime
from google.appengine.api import mail, app_identity
from api import TicTacToeApi

from models import User, TicTac


class SendReminderEmail(webapp2.RequestHandler):

    def get(self):
        """Send a reminder email to each User with an email about active games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        game_users = TicTac.query(projection=["user"], distinct =True,
                        TicTac.last_step <
                        (datetime.datetime.now() -
                         datetime.timedelta(hours=12)),
                        TicTac.game_over != True,
                        TicTac.cancelled != True).order(user)

        for user in game_users:
            user_to_mail = User.query(User.key == user.key)
            subject = 'This is a reminder!'
            body = '''Hello {},
                      You have not made a move in your active game(s)
                      for more than 12 hours!'''.format(user_to_mail.name)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user_to_mail.email,
                           subject,
                           body)


class UpdateAverageSteps(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        TicTacToeApi._cache_average_steps()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_steps', UpdateAverageSteps),
], debug=True)
