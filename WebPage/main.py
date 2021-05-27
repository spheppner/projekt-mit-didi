from flask import Flask, redirect, url_for, render_template, request, session, flash
from werkzeug.datastructures import ImmutableOrderedMultiDict
import os
import login
import json
import logging
import motorcontrol

image_folder = os.path.join("static", "images")

app = Flask(__name__)
app.config["image_folder"] = image_folder
app.secret_key = "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ"

logging.basicConfig(level=logging.DEBUG)


class Motor:
    def __init__(self):
        self.motorposition = 0
        self.motor = motorcontrol.Nema17Motor((14, 15, 18), 20, 21, 100, 200, 0.05)


motor = Motor()

plotter = motorcontrol.Plotter()



class WebPage:

    pages = {
        "home": {"page_header": "Home", "page_id": 0},
        "login": {"page_header": "Login", "page_id": 1},
        "register": {"page_header": "Register", "page_id": 2},
        "control": {"page_header": "Control", "page_id": 3},
        "page_not_found": {"page_header": "Page Not Found", "page_id": 3},
    }

    def __init__(self):
        print("Server initialized!")

    @app.route("/")
    def mainPage():
        if "current_page" not in session:
            session["current_page"] = "home"
        if "loggedin" not in session:
            session["loggedin"] = ""
        if "access_level" not in session:
            session["access_level"] = 0
        logo_filename = os.path.join(app.config["image_folder"], "logo_weiss.png")
        return render_template(
            "index.html",
            page_infos=WebPage.pages[session["current_page"]],
            logo_path=logo_filename,
            logged_in=session["loggedin"],
            access_level=session["access_level"],
        )

    @app.route("/<page_name>")
    def pageLoader(page_name):
        if page_name == "favicon.ico":
            return redirect(url_for("mainPage"))
        if page_name != "rsubmit" and page_name != "register":
            session.pop("_flashes", None)
        session["current_page"] = page_name
        if page_name not in WebPage.pages:
            session["current_page"] = "page_not_found"
        return redirect(url_for("mainPage"))

    @app.route("/rsubmit", methods=["POST", "GET"])
    def rsubmit():
        if request.method == "POST":
            rname = request.form["rname"]
            rpass = request.form["rpass"]
            remail = request.form["remail"]
            print(rname, rpass, remail)
        if rname == "" or rpass == "" or remail == "":
            flash("Fill out all fields!")
            return redirect(url_for("mainPage"))

        reg = login.register(rname, rpass)
        if reg == "user_exists":
            flash("User already exists!", "info")
            return redirect(url_for("mainPage"))

        with open("users.json", "r") as ur:
            cf = json.load(ur)
        cf[list(cf)[0]].append(remail)
        with open("users.json", "w") as uf:
            json.dump(cf, uf)

        session["current_page"] = "home"
        return redirect(url_for("mainPage"))

    @app.route("/lsubmit", methods=["POST", "GET"])
    def lsubmit():
        if request.method == "POST":
            lname = request.form["lname"]
            lpass = request.form["lpass"]

            if login.login(lname, lpass) == lname:
                session["loggedin"] = lname
                session["access_level"] = 1
            else:
                flash("Wrong username or password", "info")
                return redirect(url_for("mainPage"))

        session["current_page"] = "home"
        return redirect(url_for("mainPage"))

    @app.route("/logout")
    def logout():
        session["loggedin"] = ""
        session["access_level"] = 0

        session["current_page"] = "home"
        return redirect(url_for("mainPage"))

    @app.route("/motorcontrol")
    def motorcontrol():
        args = request.args.to_dict(flat=False)
        argkeys = list(args.keys())
        argvalues = list(args.values())

        if "start" in argkeys:
            plotter.start()
        if "getposition" in argkeys:
            position = (plotter.x, plotter.y)
            app.logger.info(position)
        if "setposition" in argkeys:
            position = args["setposition"]
            positionsplit = position#.split(",")
            position = (positionsplit[0],positionsplit[1])
            app.logger.info(position)
            plotter.queue.put({"command":"move-xy", "attributes":position})
            app.logger.info(position)

        return ("", 204)

    @app.route("/get_to_position")
    def get_to_position():
        position = request.args.get("position")

        delta = position - motor.motorposition
        motor.motorposition = position
        motor.motor.moveMotor(delta, 100)

        app.logger.info(position)

        return ("", 204)  # No need to return anything

if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True, debug=True)
    WebPage()
