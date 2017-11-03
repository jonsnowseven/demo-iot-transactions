template = {
  "swagger": "2.0",
  "uiversion": "3",
  "info": {
    "title": "Fraud Detection Demo",
    "description": "API documentation.\n\nStreaming resources at:\n\n\t/stream/start\n\nand \n\n\t/stream/stop",
    "contact": {
      "responsibleOrganization": "Marionete",
      "responsibleDeveloper": "João Neves",
      "email": "joao.neves@marionete.co.uk"
    },
    "version": "0.0.1"
  },
  # "host": "fathomless-taiga-13662.herokuapp.com",  # overrides localhost:500
  "basePath": "/",  # base bash for blueprint registration
  "schemes": [
    "http",
    "https"
  ],
  "security": {
     "Bearer": ["requirements", "companies"]
   },
  "securityDefinitions": {
      "Bearer": {
         "type": "apiKey",
         "name": "Authorization",
          "bearerFormat": "JWT"
      }
  }
}
