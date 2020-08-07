#!/usr/bin/env python3

from aws_cdk import core

from game_api.game_api_stack import GameApiStack


app = core.App()
GameApiStack(app, "game-api")

app.synth()
