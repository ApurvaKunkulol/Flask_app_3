import random
import string
import logging

from bson import json_util
from flask import Flask, request
from flask_pymongo import PyMongo
from flask_restplus import Api, Resource
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest

from constants import local_connection_string


app = Flask(__name__)
app.config["MONGO_URI"] = local_connection_string
mongo_conn = PyMongo(app)
api = Api(app)


@api.route("/api/v0.1/<string:prod_id>")
class EditProductAPI(Resource):
    def get(self, prod_id):
        """
        Description: Will get the product information associated with the passed product ID.
        Parameters:
            prod_id: The product ID of the product whose information is required.
        Return:
             JSON containing the information of the user.
             e.g:
             {
                "_id" : ObjectId("5e4a81de2c2fc0c10b7d336e"),
                "firstname" : "Akshay",
                "lastname" : "Panini",
                "email" : "panini.akshay@gmail.com",
                "designation" : "student",
                "address" : "Varanasi, India.",
                "website" : "https://someURL.com",
                "qualification" : "M. Phil (History)"
            }

            In case of an error it'll still return a JSON indicating the unsuccessful status of the operation.
            e.g: {"error": "No user found with the given email."}
        """

        tmp = mongo_conn.db.user.find({"prod_id": prod_id})
        try:
            existing_product = tmp[0]
        except IndexError as index_err:
            logging.error("Error while accessing records for existing product.", exc_info=True)
            return {"status": "error", "description": "No product found with the given email."}
        except Exception as ex:
            logging.error("Error while accessing existing records.", exc_info=True)
            return {"status": "error", "description": "Exception while retrieving the product: {}".format(str(ex))}
        if existing_product:
            return json_util.dumps({"status": "success", "description": "", "product_info": existing_product})

    def put(self, prod_id):
        """
        Description: A PUT function whose primary objective is to update information of the product with the information
                     received in the request body.
                     However, if there is no existing record of the product, it will insert a new record for the
                     product.
                     An example of the updated info would be:
                        {
                            "updated_info": {
                                "firstname" : "Apurva",
                                "lastname" : "Kunkulol",
                                "email" : "kunkulol.apurva@gmail.com",
                                "designation" : "student",
                                "address" : "Bombay, India.",
                                "website" : "https://someURL.com",
                                "qualification" : "M. Arch (Restoration Architecture)"
                            }

                        }
        Parameter(s):
            prod_id: String containing the product ID of the user whose information to edit.
        Return:
            JSON containing the status of the operation.
            example: { "status": "Record updated successfully." }
        """
        try:
            if prod_id:
                tmp = mongo_conn.db.user.find({"email": prod_id})
                try:
                    existing_record = tmp[0]
                    updated_info = request.json.get("updated_info")
                    if updated_info:
                        for key, value in updated_info.items():
                            if key == "prod_id":
                                continue
                            existing_record[key] = value
                        result = mongo_conn.db.user.update({"prod_id": prod_id}, existing_record)
                        if "ok" in result:
                            return {"status": "success", "description": "Record updated successfully."}
                        else:
                            return {"status": "error", "description": "Could not update record successfully. "
                                                                      "Status description: {}".format(result)}
                    else:
                        return {"status": "error", "description": "Please supply information to update."}
                except IndexError as idx_err:
                    logging.warning("No previous record exists for {}. Inserting a new one.".format(prod_id))
            else:
                return {"status": "error", "description": "product ID not supplied."}
        except Exception as ex:
            logging.error("Error while updating information about {}".format(prod_id), exc_info=True)
            return {"status": "error", "description": "Error while updating information. "
                                                      "Please contact support for more information."}

    def delete(self, prod_id):
        """
        Description:
            A DELETE function to delete product information associated with the prod_id supplied.
        Parameter(s):
            prod_id: Product ID of the product whose record to delete.
        Returns:
            JSON containing the status of the operation.
        """
        if prod_id:
            try:
                result = mongo_conn.db.user.delete_one({"prod_id": prod_id})
                deleted_count = result.deleted_count
                if deleted_count == 1:
                    return {"status": "success", "description": "Successfully deleted information for product "
                                                                "{}.".format(prod_id)}
                elif deleted_count < 1:
                    return {"status": "error", "description": "Product does not exist for ID {}.".format(prod_id)}
            except Exception as ex:
                logging.error("Error while deleting info for the product {}".format(prod_id), exc_info=True)
                return {"status": "error", "description": "Error while deleting info for the ID {}".format(prod_id)}
        else:
            return {"status": "error", "description": "Please provide the Prodcut ID of the product whose "
                                                      "record to delete."}


@api.route("/api/v0.1/create")
class CreateProduct(Resource):

    def post(self):
        """
        Will only create a new record for the product if none exists.
        Make a request from POSTMAN(or any other REST client for that matter.) in the following form:

        URL: 127.0.0.1:5000/hello_api/create (replace the loopback IP with the IP of the server that you're
                                              running from)
        BODY of the request:
            As shown below.
            Please select Body > raw > JSON in the UI of the REST Client.
        Arguments:
            Dictionary/JSON inside the `.json` attribute of the request.
            e.g:
                {
                    "productname" : "abc",
                    "make" : "some Company",
                    "model" : "17A56UI",
                    "manufacturing address" : "someplace, somecountry.",
                    "website" : "https://someURL.com",
                }

        Return:
            JSON containing the status of the operation.
        """
        try:
            if request.json:
                try:
                    try:
                        product_info = request.get_json()
                        random_letters = string.ascii_lowercase
                        prod_id = "{}".format("".join(random.choice(random_letters) for i in range(4)))
                        product_info["prod_id"] = prod_id
                        mongo_conn.db.product_info.insert(product_info)
                        return {"status": "success", "description": "Successfully inserted record for product. "
                                                                    "ID: {}".format(prod_id)}
                    except DuplicateKeyError as dup_key_err:
                        logging.error("Another record with the same product id/make found.", exc_info=True)
                        return {"status": "error",
                                "description": "product id/make already exists. Please provide another unique "
                                               "product id or make."}
                    except Exception as ex:
                        logging.error("Error while attempting to retrieve existing record", exc_info=True)
                        return {"status": "error",
                                "description": "Error while inserting information for the product."}
                except Exception as ex:
                    logging.error("Error while inserting record for product.", exc_info=True)
                    return {"status": "error", "description": "Error while inserting record."}
        except BadRequest as bad_req_err:
            logging.error("Input error.", exc_info=True)
            return {"status": "error", "description": "No or bad input provided."}


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=7000)



