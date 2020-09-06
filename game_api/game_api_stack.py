from aws_cdk import (
    core, 
    aws_dynamodb as db,
    aws_apigateway,
    aws_lambda,
    aws_s3 as s3,
    aws_iam as iam
)
import os
import api_models as models

LIBRARY_PATH = os.path.abspath("layers")


class GameApiStack(core.Stack):
    layers = None
    buckets = None
    lambdas = None
    models = None
    cors_integration = None
    authorizers = None
    rest_api: aws_apigateway.LambdaRestApi = None

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        self.create_layers()
        self.create_lambdas()
        self.create_tables()
        self.create_buckets()


        # Create api gateway 
        self.rest_api = aws_apigateway.LambdaRestApi(
            self,
            "minh-intern-game-api",
            handler=self.lambdas["user_login"],
            proxy=False,
            endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
            deploy_options={
                "stage_name": "v1"
            }
        )

        self.cors_integration = aws_apigateway.LambdaIntegration(
            self.lambdas["cors_handler"],
            proxy=True
        )

        self.add_authorizers()
        self.add_models_to_rest()

        # Define route of every resource
        self.define_login_route()
        self.define_acquire_access_token()
        self.define_user_route()
        self.define_game_map_route()
        self.define_gamestate_route()


    def create_tables(self):
        """
        Create tables for the app.
        """

        # user table
        user_table = db.Table(
            self,
            "minh-intern.user",
            partition_key= db.Attribute(name="user_id", type=db.AttributeType.STRING),
            table_name="minh-intern.user"
        )
        user_table.add_global_secondary_index(
            index_name="user-unique-username-project-all",
            partition_key=db.Attribute(name="username", type=db.AttributeType.STRING),
            projection_type=db.ProjectionType.ALL
        )
        user_table.grant(self.lambdas["user_login"], "dynamodb:*")
        user_table.grant(self.lambdas["create_user"], "dynamodb:*")
        user_table.grant(self.lambdas["get_user_by_id"], "dynamodb:*")
        user_table.grant(self.lambdas["update_user_account"], "dynamodb:*")
        user_table.grant(self.lambdas["update_user_profile"], "dynamodb:*")
        user_table.grant(self.lambdas["acquire_access_token"], "dynamodb:*")


        # game map table
        game_map_table = db.Table(
            self,
            "minh-intern.game_map",
            partition_key= db.Attribute(name="created_by", type=db.AttributeType.STRING),
            sort_key=db.Attribute(name="last_edited", type=db.AttributeType.STRING),
            table_name="minh-intern.game_map"
        )
        game_map_table.add_global_secondary_index(
            index_name="game-map-unique-map-id",
            partition_key=db.Attribute(name="id", type=db.AttributeType.STRING),
            projection_type=db.ProjectionType.ALL
        )
        game_map_table.grant(self.lambdas["create_map"], "dynamodb:*")

        gamestate_table = db.Table(
            self,
            "minh-intern.game_state",
            partition_key= db.Attribute(name="user", type=db.AttributeType.STRING),
            sort_key=db.Attribute(name="game_map", type=db.AttributeType.STRING),
            table_name="minh-intern.game_state"
        )
        gamestate_table.grant(self.lambdas["get_list_gamestate_pagination"], "dynamodb:*")
        
        table_row_count = db.Table(
            self,
            "minh-intern.table_row_count",
            partition_key=db.Attribute(name="table_name", type=db.AttributeType.STRING),
            table_name="minh-intern.table_row_count"
        )
        table_row_count.grant(self.lambdas["create_map"], "dynamodb:*")
        table_row_count.grant(self.lambdas["get_list_map_pagination"], "dynamodb:*")


    def create_lambdas(self):
        """
        Create all lambdas and attach them to `lambdas` variable and access as dict.
        """

        self.lambdas = {}

        self.lambdas["cors_handler"] = aws_lambda.Function(
            self,
            "minh-intern-cors-handler",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="cors.handler",
            function_name="minh-intern-cors-handler",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaCorsHandler",                
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            )
        )

        self.lambdas["user_login"] = aws_lambda.Function(
            self,
            "minh-intern-user-login",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="login.handler",
            layers=[self.layers["custom_modules"], self.layers["bcrypt"], self.layers['pyjwt']],
            function_name="minh-intern-user-login",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            timeout=core.Duration.seconds(10),
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaLogin",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user",
                "JWT_SECRET_KEY": "gameapi"
            }
        )
        
        self.lambdas["create_user"] = aws_lambda.Function(
            self,
            "minh-intern-create-user",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="create_user.handler",
            layers=[self.layers["custom_modules"], self.layers["bcrypt"], self.layers["pyjwt"]],
            function_name="minh-intern-create-user",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaCreateUser",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user",
                "JWT_SECRET_KEY": "gameapi",
                "S3_BUCKET_NAME": "minh-intern.game-bucket",
                "S3_USER_FOLDER_NAME": "user"
            },
            timeout=core.Duration.seconds(10)
        )

        self.lambdas["get_user_by_id"] = aws_lambda.Function(
            self,
            "minh-intern-get_user_by_id",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="get_user_by_id.handler",
            layers=[self.layers["bcrypt"], self.layers["pyjwt"]],
            function_name="minh-intern-get_user_by_id",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaGetUserById",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user"
            }
        )

        self.lambdas["update_user_account"] = aws_lambda.Function(
            self,
            "minh-intern-update_user_account",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="update_user_account.handler",
            layers=[self.layers["bcrypt"], self.layers["pyjwt"]],
            function_name="minh-intern-update_user_account",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaUpdateAccount",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user"
            },
            timeout=core.Duration.seconds(10)
        )

        self.lambdas["update_user_profile"] = aws_lambda.Function(
            self,
            "minh-intern-update_user_profile",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="update_user_profile.handler",
            layers=[self.layers["bcrypt"], self.layers["pyjwt"]],
            function_name="minh-intern-update_user_profile",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaUpdateProfile",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user"
            }
        )

        self.lambdas["update_user_picture"] = aws_lambda.Function(
            self,
            "minh-intern-update_user_picture",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="update_user_picture.handler",
            function_name="minh-intern-update_user_picture",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaUpdateUserPicture",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user",
                "S3_BUCKET_DOMAIN": "https://s3.amazonaws.com"
            }
        )

        
        self.lambdas["acquire_access_token"] = aws_lambda.Function(
            self,
            "minh-intern-acquire_access_token",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="acquire_access_token.handler",
            layers=[self.layers["custom_modules"], self.layers["pyjwt"]],
            function_name="minh-intern-acquire_access_token",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaAcquireAccessToken",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user",
                "JWT_SECRET_KEY": "gameapi",
                "S3_BUCKET_NAME": "minh-intern.game-bucket"
            }
        )

        self.lambdas["create_map"] = aws_lambda.Function(
            self,
            "minh-intern-create_map",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="create_map.handler",
            layers=[self.layers["pyjwt"], self.layers["custom_modules"]],
            function_name="minh-intern-create_map",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaCreateMap",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.game_map",
                "S3_BUCKET_NAME": "minh-intern.game-bucket",
                "S3_MAP_FOLDER": "gamemap",
                "ROW_COUNT_TABLE_NAME": "minh-intern.table_row_count"
            }
        )

        self.lambdas["create_map_trigger"] = aws_lambda.Function(
            self,
            "minh-intern-create_map_trigger",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="create_map_trigger.handler",
            function_name="minh-intern-create_map_trigger",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaCreateMapTrigger",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.game_map",
                "S3_BUCKET_DOMAIN": "https://s3.amazonaws.com",
            }
        )

        self.lambdas["update_map"] = aws_lambda.Function(
            self,
            "minh-intern-update_map",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="update_map.handler",
            layers=[self.layers["pyjwt"], self.layers["custom_modules"]],
            function_name="minh-intern-update_map",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaUpdateMap",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.game_map",
                "S3_BUCKET_NAME": "minh-intern.game-bucket",
                "S3_MAP_FOLDER": "gamemap"
            }
        )

        self.lambdas["authorize_user"] = aws_lambda.Function(
            self,
            "minh-intern-authorize_user",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="authorize_user.handler",
            layers=[self.layers["pyjwt"], self.layers["custom_modules"]],
            function_name="minh-intern-authorize_user",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaAuthorizeUser",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.user",
                "JWT_SECRET_KEY": "gameapi"
            }
        )

        self.lambdas["get_list_map_pagination"] = aws_lambda.Function(
            self,
            "minh-intern-get_list_map_pagination",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="get_list_map_pagination.handler",
            layers=[self.layers["pyjwt"], self.layers["custom_modules"]],
            function_name="minh-intern-get_list_map_pagination",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaGetListMapPagination",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.game_map",
                "PAGINATION_PAGE_SIZE": "3",
                "ROW_COUNT_TABLE_NAME": "minh-intern.table_row_count"
            }
        )

        self.lambdas["get_map_by_id"] = aws_lambda.Function(
            self,
            "minh-intern-get_map_by_id",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="get_map_by_id.handler",
            function_name="minh-intern-get_map_by_id",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaGetMapById",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "TABLE_NAME": "minh-intern.game_map"
            }
        )

        self.lambdas["get_list_gamestate_pagination"] = aws_lambda.Function(
            self,
            "minh-intern-get_list_gamestate_pagination",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="get_list_gamestate_pagination.handler",
            function_name="minh-intern-get_list_gamestate_pagination",
            layers=[self.layers["pyjwt"], self.layers["custom_modules"]],
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaGetListGameStatePagination",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "GAMESTATE_TABLE_NAME": "minh-intern.game_state",
                "GAMEMAP_TABLE_NAME": "minh-intern.game_map",
                "ROW_COUNT_TABLE_NAME": "minh-intern.table_row_count",
                "PAGINATION_PAGE_SIZE": "3"
            }
        )

        self.lambdas["create_gamestate"] = aws_lambda.Function(
            self,
            "minh-intern-create_gamestate",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="create_gamestate.handler",
            function_name="minh-intern-create_gamestate",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaCreateGameState",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "GAMESTATE_TABLE_NAME": "minh-intern.game_state",
                "GAMEMAP_TABLE_NAME": "minh-intern.game_map"
            }
        )

        self.lambdas["get_gamestate_by_mapid_userid"] = aws_lambda.Function(
            self,
            "minh-intern-get_gamestate_by_mapid_userid",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="get_gamestate_by_mapid_userid.handler",
            function_name="minh-intern-get_gamestate_by_mapid_userid",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=iam.Role.from_role_arn(
                self,
                "minh-intern-LambdaGetGameStateByMapIdAndUserId",
                role_arn="arn:aws:iam::573915606947:role/ir.us.intern"
            ),
            environment={
                "GAMESTATE_TABLE_NAME": "minh-intern.game_state",
                "GAMEMAP_TABLE_NAME": "minh-intern.game_map"
            }
        )

    
    def create_layers(self):
        """
        Create all necessary layers for the stack through `layers` variable and access as `DictType`.
        """

        self.layers = {}
        self.layers['pyjwt'] = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "minhnd-pyjwt",
            "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-PyJWT:1"
        )
        self.layers["bcrypt"] = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "minh-intern-bcrypt",
            "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-bcrypt:6"
        )
        self.layers["custom_modules"] = aws_lambda.LayerVersion(
            self,
            "minh-intern-custom_modules",
            code=aws_lambda.Code.from_asset("./layers/__custom__.zip"),
            layer_version_name="minh-intern-custom_modules"
        )


    def create_buckets(self):
        """
        Define s3 bucket for the stack through `buckets` variable and access as `DictType`.
        """

        cors_allowed_methods = [
            s3.HttpMethods.DELETE,
            s3.HttpMethods.PUT,
            s3.HttpMethods.POST,
            s3.HttpMethods.HEAD,
            s3.HttpMethods.GET
        ]
        self.buckets = {}
        self.buckets['game_bucket'] = s3.Bucket(
            self,
            "minh-intern.game-bucket",
            bucket_name="minh-intern.game-bucket",
            public_read_access=True,
            cors=[s3.CorsRule(
                allowed_methods=cors_allowed_methods,
                allowed_headers=["*"],
                allowed_origins=["*"]
            )]
        )


    def add_models_to_rest(self) -> None:
        """
        Define api models for the stack and attach to `models` variable and accessed as `DictType`
        """

        if self.rest_api is None:
            raise Exception("The api is None")

        self.models = {}

        self.models["login_model"] = self.rest_api.add_model("UserLoginModel", **models.login_model)
        self.models["create_user_model"] = self.rest_api.add_model("CreateUserModel", **models.create_user_model)
        self.models["update_user_model"] = self.rest_api.add_model("UpdateUserModel", **models.update_user_model)
        self.models["profile_model"] = self.rest_api.add_model("ProfileModel", **models.profile_model)

    
    def add_authorizers(self) -> None:
        """
        Define authorizers for the application.\n
        The authorizers are accessed through `self.authorizers` 
        """

        self.authorizers = {}

        self.authorizers["user_authorizer"] = aws_apigateway.TokenAuthorizer(
            self,
            "minh-intern-user_authorizer",
            authorizer_name="minh-intern-user_authorizer",
            handler=self.lambdas["authorize_user"]
        )


    def define_login_route(self):
        login_lambda_integration = aws_apigateway.LambdaIntegration(
            self.lambdas["user_login"],
            proxy=True
        )

        login_resource = self.rest_api.root.add_resource("login")
        
        login_resource.add_method(
            "OPTIONS", 
            integration=self.cors_integration
        )

        login_resource.add_method(
            "POST", 
            integration=login_lambda_integration,
            request_validator=aws_apigateway.RequestValidator(
                self,
                "user_login_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="user_login_validator",
                validate_request_body=True
            ),
            request_models={
                "application/json": self.models["login_model"]
            }
        )

    def define_acquire_access_token(self):
        resource = self.rest_api.root.add_resource("acquireaccesstoken")

        resource.add_method(
            "OPTIONS",
            integration=self.cors_integration
        )

        resource.add_method(
            "POST",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["acquire_access_token"],
                proxy=True
            )
        )

    
    def define_user_route(self):
        user_resource = self.rest_api.root.add_resource("user")
        specific_user_resource = user_resource.add_resource("{user_id}")
        user_profile_resource = specific_user_resource.add_resource("profile")
        
        user_resource.add_method(
            "OPTIONS", 
            integration=self.cors_integration
        )

        user_resource.add_method(
            "POST", 
            integration = aws_apigateway.LambdaIntegration(
                self.lambdas["create_user"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "create_user_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="create_user_validator",
                validate_request_body=True
            ),
            request_models={
                "application/json": self.models["create_user_model"]
            }
        )

        specific_user_resource.add_method(
            "OPTIONS",
            integration=self.cors_integration
        )

        specific_user_resource.add_method(
            "GET",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["get_user_by_id"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "get_user_by_id_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="get_user_by_id_validator",
                validate_request_parameters=True
            ),
            authorizer=self.authorizers["user_authorizer"],
            request_parameters={
                "method.request.path.user_id": True
            }
        )

        specific_user_resource.add_method(
            "PUT",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["update_user_account"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "update_user_account_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="update_user_account_validator",
                validate_request_body=True,
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.path.user_id": True
            },
            request_models={
                "application/json": self.models["update_user_model"]
            },
            authorizer=self.authorizers["user_authorizer"]
        )

        user_profile_resource.add_method(
            "PUT",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["update_user_profile"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "update_user_profile_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="update_user_profile_validator",
                validate_request_body=True,
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.path.user_id": True
            },
            request_models={
                "application/json": self.models["profile_model"]
            },
            authorizer=self.authorizers["user_authorizer"]
        )


    def define_game_map_route(self):
        map_resource = self.rest_api.root.add_resource("map")
        specific_map_resource = map_resource.add_resource("{id}")

        map_resource.add_method(
            "OPTIONS",
            integration=self.cors_integration
        )

        map_resource.add_method(
            "POST",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["create_map"],
                proxy=True
            ),
            authorizer=self.authorizers["user_authorizer"]
        )

        map_resource.add_method(
            "GET",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["get_list_map_pagination"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "get_list_map_pagination_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="get_list_map_pagination_validator",
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.querystring.page": True
            },
            authorizer=self.authorizers["user_authorizer"]
        )

        specific_map_resource.add_method(
            "OPTIONS",
            integration=self.cors_integration
        )

        specific_map_resource.add_method(
            "GET",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["get_map_by_id"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "get_map_by_id_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="get_map_by_id_validator",
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.path.id": True
            },
            authorizer=self.authorizers["user_authorizer"]
        )

        specific_map_resource.add_method(
            "PUT",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["update_map"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "update_map_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="update_map_validator",
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.path.id": True
            },
            authorizer=self.authorizers["user_authorizer"]
        )
    

    def define_gamestate_route(self):
        gamestate_resource = self.rest_api.root.add_resource("gamestate")
        specific_gamestate_resource = gamestate_resource.add_resource("{map_id}")

        gamestate_resource.add_method(
            "OPTIONS",
            integration=self.cors_integration
        )

        gamestate_resource.add_method(
            "POST",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["create_gamestate"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "create_gamestate_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="create_gamestate_validator",
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.querystring.map_id": True,
                "method.request.querystring.state": True
            },
            authorizer=self.authorizers["user_authorizer"]
        )

        gamestate_resource.add_method(
            "GET",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["get_list_gamestate_pagination"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "get_list_gamestate_pagination_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="get_list_gamestate_pagination_validator",
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.querystring.page": True
            },
            authorizer=self.authorizers["user_authorizer"]
        )

        specific_gamestate_resource.add_method(
            "OPTIONS",
            integration=self.cors_integration
        )

        specific_gamestate_resource.add_method(
            "GET",
            integration=aws_apigateway.LambdaIntegration(
                self.lambdas["get_gamestate_by_mapid_userid"],
                proxy=True
            ),
            request_validator=aws_apigateway.RequestValidator(
                self,
                "get_gamestate_by_mapid_userid_validator_prud",
                rest_api=self.rest_api,
                request_validator_name="get_gamestate_by_mapid_userid_validator",
                validate_request_parameters=True
            ),
            request_parameters={
                "method.request.path.map_id": True,
            },
            authorizer=self.authorizers["user_authorizer"]
        )