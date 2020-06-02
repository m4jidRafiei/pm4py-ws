import base64
import os
import random
import string
import traceback
from threading import Semaphore

from flask import Flask, request, jsonify
from flask_cors import CORS

from pm4pywsconfiguration import configuration as Configuration
from pm4pyws.log_manager import factory as session_manager_factory
from pm4pyws.user_iam import factory as user_iam_factory
from pm4pyws.requests_logging import factory as logging_factory
from pm4pyws.util import constants

import socket

import logging

from pm4pyws.privacy.roles import apply_privacy_aware
from pm4pyws.privacy.connector import apply_connector
from pm4pyws.privacy.tklc import apply_tklc

ex = logging_factory.apply()
um = user_iam_factory.apply(ex)
lh = session_manager_factory.apply(ex, variant=Configuration.log_manager_default_variant)
lh.set_user_management(um)


class Commons:
    semaphore_matplot = Semaphore(1)


def clean_expired_sessions():
    """
    Cleans expired sessions
    """
    um.clean_expired_sessions()
    sessions = um.get_all_sessions()
    lh.remove_unneeded_sessions(sessions)


def do_login(user, password):
    """
    Logs in a user and returns a session id

    Parameters
    ------------
    user
        Username
    password
        Password

    Returns
    ------------
    session_id
        Session ID
    """
    ret = um.do_login(user, password)

    clean_expired_sessions()

    return ret


def check_session_validity(session_id):
    """
    Checks the validity of a session

    Parameters
    ------------
    session_id
        Session ID

    Returns
    ------------
    boolean
        Boolean value
    """
    if Configuration.enable_session:
        clean_expired_sessions()

        validity = um.check_session_validity(session_id)
        return validity
    return True


def get_user_from_session(session_id):
    """
    Gets the user from the session

    Parameters
    ------------
    session_id
        Session ID

    Returns
    ------------
    user
        User ID
    """
    if Configuration.enable_session:
        user = um.get_user_from_session(session_id)
        return user
    return None


class PM4PyServices:
    app = Flask(__name__, static_url_path='', static_folder=Configuration.static_folder)
    app.add_url_rule(app.static_url_path + '/<path:filename>', endpoint='static',
                     view_func=app.send_static_file)
    CORS(app)

    def load_log(self, log_name, file_path, parameters=None):
        """
        Loads an event log inside the known handlers

        Parameters
        ------------
        log_name
            Log name
        file_path
            Full path (in the services machine) to the log
        parameters
            Possible parameters
        """
        lh.load_log_static(log_name, file_path, parameters=parameters)

    def serve(self, host="0.0.0.0", port="5000", threaded=True, ssl_context=None):
        clean_expired_sessions()
        if ssl_context is None:
            self.app.run(host=host, port=port, threaded=threaded)
        else:
            self.app.run(host=host, port=port, threaded=threaded, ssl_context=ssl_context)


@PM4PyServices.app.route("/getProcessSchema", methods=["GET"])
def get_process_schema():
    """
    Gets the process schema in the wanted format

    Returns
    ------------
    dictio
        JSONified dictionary that contains in the 'base64' entry the SVG representation
        of the process schema. Moreover, 'model' contains the process model (if the output is meaningful)
        and 'format' contains the format
    :return:
    """
    clean_expired_sessions()

    dictio = {}
    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info(
        "get_process_schema start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            Commons.semaphore_matplot.acquire()
            try:
                # reads the decoration
                decoration = request.args.get('decoration', default='freq', type=str)
                # reads the typeOfModel
                type_of_model = request.args.get('typeOfModel', default='dfg', type=str)
                # reads the simplicity
                simplicity = request.args.get('simplicity', default=constants.DEFAULT_DEC_FACTOR, type=float)
                variant = type_of_model + "_" + decoration
                parameters = {"decreasingFactor": simplicity}
                handler = lh.get_handler_for_process_and_session(process, session)
                filters_chain = handler.get_filters_chain_repr()
                ps_repr = process + "@@" + variant + "@@" + str(simplicity) + "@@" + filters_chain
                saved_obj = lh.get_object_memory(ps_repr) if Configuration.enable_process_caching else None
                if saved_obj is not None:
                    base64 = saved_obj[0]
                    model = saved_obj[1]
                    format = saved_obj[2]
                    this_handler = saved_obj[3]
                    activities = saved_obj[4]
                    start_activities = saved_obj[5]
                    end_activities = saved_obj[6]
                    gviz_base64 = saved_obj[7]
                    graph_rep = saved_obj[8]
                    type_of_model = saved_obj[9]
                    decoration = saved_obj[10]
                    second_model = saved_obj[11]
                    second_format = saved_obj[12]
                    activity_key = saved_obj[13]
                    log_summary = saved_obj[14]
                else:
                    base64, model, format, this_handler, activities, start_activities, end_activities, gviz_base64, graph_rep, type_of_model, decoration, second_model, second_format, activity_key, log_summary = handler.get_schema(
                        variant=variant,
                        parameters=parameters)
                    lh.save_object_memory(ps_repr, [base64, model, format, this_handler, activities, start_activities,
                                                    end_activities, gviz_base64, graph_rep, type_of_model, decoration,
                                                    second_model, second_format, activity_key, log_summary])
                if model is not None:
                    if type(model) is not str:
                        model = model.decode('utf-8')

                dictio = {"base64": base64.decode('utf-8'), "model": model, "format": format, "handler": this_handler,
                          "activities": activities,
                          "start_activities": start_activities, "end_activities": end_activities,
                          "gviz_base64": gviz_base64.decode('utf-8'), "graph_rep": graph_rep,
                          "type_of_model": type_of_model, "decoration": decoration,
                          "second_model": second_model, "second_format": second_format, "activity_key": activity_key}
                for key in log_summary:
                    dictio[key] = log_summary[key]
            except:
                logging.error(traceback.format_exc())
            Commons.semaphore_matplot.release()

            logging.info(
                "get_process_schema complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))
    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/getNumericAttributeGraph", methods=["GET"])
def get_numeric_attribute_graph():
    """
    Gets the numeric attribute graph

    Returns
    -------------
    dictio
        JSONified dictionary that contains in the 'base64' entry the SVG representation
        of the case duration graph
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)
    # reads the requested attribute
    attribute = request.args.get('attribute', type=str)

    logging.info(
        "get_numeric_attribute_graph start session=" + str(session) + " process=" + str(process) + " attribute=" + str(
            attribute))

    dictio = {}
    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            Commons.semaphore_matplot.acquire()
            try:
                base64, gviz_base64, ret = lh.get_handler_for_process_and_session(process,
                                                                                  session).get_numeric_attribute_svg(
                    attribute)
                dictio = {"base64": base64.decode('utf-8'), "gviz_base64": gviz_base64.decode('utf-8'), "points": ret}
            except:
                logging.error(traceback.format_exc())
                dictio = {"base64": "", "gviz_base64": "", "points": []}
            Commons.semaphore_matplot.release()

        logging.info(
            "get_numeric_attribute_graph start session=" + str(session) + " process=" + str(
                process) + " attribute=" + str(
                attribute) + " user=" + str(user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/getCaseDurationGraph", methods=["GET"])
def get_case_duration():
    """
    Gets the Case Duration graph

    Returns
    ------------
    dictio
        JSONified dictionary that contains in the 'base64' entry the SVG representation
        of the case duration graph
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_case_duration start session=" + str(session) + " process=" + str(process))

    dictio = {}
    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            Commons.semaphore_matplot.acquire()
            try:
                base64, gviz_base64, ret = lh.get_handler_for_process_and_session(process,
                                                                                  session).get_case_duration_svg()
                data_x = []
                data_y = []
                for i in range(len(ret)):
                    data_x.append(ret[i][0])
                    data_y.append(ret[i][1])

                dictio = {"base64": base64.decode('utf-8'), "gviz_base64": gviz_base64.decode('utf-8'), "points": ret,"points_x":data_x, "points_y":data_y}
            except:
                logging.error(traceback.format_exc())
                dictio = {"base64": "", "gviz_base64": "", "points": [],"points_x":[],"points_y":[]}
            Commons.semaphore_matplot.release()

        logging.info(
            "get_case_duration start session=" + str(session) + " process=" + str(process) + " user=" + str(user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/getEventsPerTimeGraph", methods=["GET"])
def get_events_per_time():
    """
    Gets the Event per Time graph

    Returns
    -------------
    dictio
        JSONified dictionary that contains in the 'base64' entry the SVG representation
        of the events per time graph
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_events_per_time start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            Commons.semaphore_matplot.acquire()
            try:
                base64, gviz_base64, ret = lh.get_handler_for_process_and_session(process,
                                                                                  session).get_events_per_time_svg()
                data_x = []
                data_y = []
                for i in range(len(ret)):
                    data_x.append(ret[i][0])
                    data_y.append(ret[i][1])

                dictio = {"base64": base64.decode('utf-8'), "gviz_base64": gviz_base64.decode('utf-8'), "points": ret,"points_x":data_x, "points_y":data_y}
            except:
                logging.error(traceback.format_exc())
                dictio = {"base64": "", "gviz_base64": "", "points": [],"points_x":[],"points_y":[]}
            Commons.semaphore_matplot.release()

        logging.info(
            "get_events_per_time complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))

    ret = jsonify(dictio)

    return ret


@PM4PyServices.app.route("/getSNA", methods=["GET"])
def get_sna():
    """
    Gets the Social Network (Pyvis) representation of the event log

    Returns
    -----------
    html
        HTML page containing the SNA representation
    """
    clean_expired_sessions()

    try:
        # reads the session
        session = request.args.get('session', type=str)
        # reads the requested process name
        process = request.args.get('process', default='receipt', type=str)
        sna = ""

        logging.info("get_sna start session=" + str(session) + " process=" + str(process))

        if Configuration.overall_enable_sna:
            if check_session_validity(session):
                user = get_user_from_session(session)
                if lh.check_user_log_visibility(user, process):
                    metric = request.args.get('metric', default='handover', type=str)
                    threshold = request.args.get('threshold', default=0.0, type=float)
                    sna = lh.get_handler_for_process_and_session(process, session).get_sna(variant=metric, parameters={
                        "weight_threshold": threshold})

                logging.info(
                    "get_sna complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))
    except:
        logging.error(traceback.format_exc())
        sna = ""

    return sna


@PM4PyServices.app.route("/getAllVariants", methods=["GET"])
def get_all_variants():
    """
    Gets all the variants from the event log

    Returns
    ------------
    dictio
        JSONified dictionary that contains in the 'variants' entry the list of variants
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)
    # reads the maximum number of variants to return
    max_no_variants = request.args.get('max_no_variants', default=constants.MAX_NO_VARIANTS_TO_RETURN, type=int)

    logging.info("get_all_variants start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            parameters = {}
            parameters["max_no_variants"] = int(max_no_variants)

            variants, log_summary = lh.get_handler_for_process_and_session(process, session).get_variant_statistics(
                parameters=parameters)
            dictio = {"variants": variants}
            for key in log_summary:
                dictio[key] = log_summary[key]
        logging.info(
            "get_all_variants complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))

    ret = jsonify(dictio)

    return ret


@PM4PyServices.app.route("/getAllCases", methods=["GET"])
def get_all_cases():
    """
    Gets all the cases from the event log

    Returns
    ------------
    dictio
        JSONified dictionary that contains in the 'cases' entry the list of cases
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    process = request.args.get('process', default='receipt', type=str)
    variant = request.args.get('variant', type=str)
    max_no_cases = request.args.get('max_no_cases', default=constants.MAX_NO_CASES_TO_RETURN, type=int)

    logging.info("get_all_cases start session=" + str(session) + " process=" + str(process) + " variant=" + str(variant))

    dictio = {}

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            parameters = {}
            if variant is not None:
                parameters["variant"] = variant
            parameters["max_ret_cases"] = int(max_no_cases)

            cases_list, log_summary = lh.get_handler_for_process_and_session(process, session).get_case_statistics(
                parameters=parameters)
            dictio = {"cases": cases_list}
            for key in log_summary:
                dictio[key] = log_summary[key]
        logging.info(
            "get_all_cases complete session=" + str(session) + " process=" + str(process) + " variant=" + str(
                variant) + " user=" + str(user))

    ret = jsonify(dictio)
    return ret

@PM4PyServices.app.route("/getAllVariantsAndCases", methods=["GET"])
def get_all_variants_and_cases():
    """
    Gets all the variants from the event log

    Returns
    ------------
    dictio
        JSONified dictionary that contains in the 'variants' entry the list of variants
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)
    # reads the maximum number of variants to return
    max_no_variants = request.args.get('max_no_variants', default=constants.MAX_NO_VARIANTS_TO_RETURN, type=int)

    logging.info("get_all_variants_and_cases start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            parameters = {}
            parameters["max_no_variants"] = int(max_no_variants)

            handler = lh.get_handler_for_process_and_session(process, session)
            variants, log_summary = handler.get_variant_statistics(parameters=parameters)
            cases_list, log_summary = handler.get_case_statistics(parameters=parameters)

            dictio = {"variants": variants, "cases": cases_list}
            for key in log_summary:
                dictio[key] = log_summary[key]
        logging.info(
            "get_all_variants_and_cases complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))

    ret = jsonify(dictio)

    return ret


@PM4PyServices.app.route("/getEvents", methods=["GET"])
def get_events():
    """
    Gets the events from a Case ID

    Returns
    -------------
    dictio
        JSONified dictionary that contains in the 'events' entry the list of events
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_events start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            caseid = request.args.get('caseid', type=str)
            events = lh.get_handler_for_process_and_session(process, session).get_events(caseid)
            i = 0
            while i < len(events):
                keys = list(events[i].keys())
                for key in keys:
                    if str(events[i][key]).lower() == "nan" or str(events[i][key]).lower() == "nat":
                        del events[i][key]
                i = i + 1
            dictio = {"events": events}

        logging.info("get_events complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/getEventsForDotted", methods=["GET"])
def get_events_per_dotted():
    """
    Gets the events for the Dotted Chart

    Returns
    -------------
    dictio
        JSONified dictionary that contains in the 'events' entry the list of events
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    process = request.args.get('process', default='receipt', type=str)
    attribute1 = request.args.get('attribute1', type=str)
    attribute2 = request.args.get('attribute2', type=str)
    attribute3 = request.args.get('attribute3', type=str)

    attributes = [attribute1, attribute2]
    if attribute3:
        attributes.append(attribute3)

    dictio = {}

    if Configuration.overall_enable_dotted_chart:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_log_visibility(user, process):
                traces, types, attributes, third_unique_values = lh.get_handler_for_process_and_session(process,
                                                                                                     session).get_events_for_dotted(
                    attributes)
                dictio = {"traces": traces, "types": types, "attributes": attributes,
                          "third_unique_values": third_unique_values}

            logging.info(
                "get_events_per_dotted complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/getSpecEventByIdx", methods=["GET"])
def get_spec_event_by_idx():
    """
    Gets the events for the Dotted Chart

    Returns
    -------------
    dictio
        JSONified dictionary that contains in the 'events' entry the list of events
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    process = request.args.get('process', default='receipt', type=str)
    index = request.args.get('index', type=int)

    dictio = {}

    if Configuration.overall_enable_dotted_chart:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_log_visibility(user, process):
                event = lh.get_handler_for_process_and_session(process, session).get_spec_event_by_idx(index)
                dictio = {"event": event}

            logging.info(
                "get_spec_event_by_idx complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/loadLogFromPath", methods=["POST"])
def load_log_from_path():
    """
    Service that loads a log from a path
    """
    clean_expired_sessions()

    if Configuration.enable_load_local_path:
        try:
            # reads the session
            session = request.args.get('session', type=str)

            logging.info("load_log_from_path start session=" + str(session))

            if check_session_validity(session):
                user = get_user_from_session(session)

                # reads the log_name entry from the request JSON
                log_name = request.json["log_name"]
                # reads the log_path entry from the request JSON
                log_path = request.json["log_path"]
                parameters = request.json["parameters"] if "parameters" in request.json else None
                print("log_name = ", log_name, "log_path = ", log_path)
                lh.load_log_static(log_name, log_path, parameters=parameters)

                logging.info("load_log_from_path complete session=" + str(session) + " user=" + str(user))

                return "OK"
        except:
            logging.error(traceback.format_exc())
            return "FAIL"
    return "FAIL"


@PM4PyServices.app.route("/getLogsList", methods=["GET"])
def get_logs_list():
    """
    Gets the list of logs loaded into the system

    Returns
    -----------
    dictio
        JSONified dictionary that contains in the 'logs' entry the list of events logs
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("get_logs_list start session=" + str(session))

    available_keys = []

    if check_session_validity(session):
        user = get_user_from_session(session)

        all_keys = lh.get_handlers().keys()

        for key in all_keys:
            if lh.check_user_log_visibility(user, key):
                available_keys.append(key)

        logging.info("get_logs_list complete session=" + str(session) + " user=" + str(user))

    return jsonify({"logs": available_keys})


@PM4PyServices.app.route("/getLogsListAdvanced", methods=["GET"])
def get_logs_list_advanced():
    """
    Gets the list of logs loaded into the system

    Returns
    -----------
    dictio
        JSONified dictionary that contains in the 'logs' entry the list of events logs
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("get_logs_list_advanced start session=" + str(session))

    available_keys = []

    if check_session_validity(session):
        user = get_user_from_session(session)

        handlers = lh.get_handlers()
        all_keys = handlers.keys()

        for key in all_keys:
            if lh.check_user_log_visibility(user, key):
                can_download = lh.check_user_enabled_download(user, key)
                can_delete = lh.can_delete(user, key)
                type = lh.get_handler_type(handlers[key])
                available_keys.append({"log_name": key, "can_download": can_download, "can_delete": can_delete, "type": type})

        logging.info("get_logs_list_advanced start session=" + str(session) + " user=" + str(user))

    return jsonify({"logs": available_keys})


@PM4PyServices.app.route("/transientAnalysis", methods=["GET"])
def do_transient_analysis():
    """
    Perform transient analysis on the log

    Returns
    ------------
    dictio
        JSONified dictionary that contains in the 'base64' entry the SVG representation
        of the events per time graph
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("do_transient_analysis start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if Configuration.overall_enable_transient:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_log_visibility(user, process):
                Commons.semaphore_matplot.acquire()
                try:
                    delay = request.args.get('delay', default=86400, type=float)

                    base64, gviz = lh.get_handler_for_process_and_session(process, session).get_transient(delay)
                    dictio = {"base64": base64.decode('utf-8'), "gviz_base64": gviz.decode('utf-8')}
                except:
                    logging.error(traceback.format_exc())
                Commons.semaphore_matplot.release()

            logging.info(
                "do_transient_analysis complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/getLogSummary", methods=["GET"])
def get_log_summary():
    """
    Gets a summary of the log

    Returns
    ------------
    log_summary
        Log summary
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_log_summary start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            dictio = lh.get_handler_for_process_and_session(process, session).get_log_summary_dictio()

        logging.info(
            "get_log_summary complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))

    ret = jsonify(dictio)
    return ret


@PM4PyServices.app.route("/downloadXesLog", methods=["GET"])
def download_xes_log():
    """
    Download the XES log

    Returns
    ------------
    xes_log
        XES log
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("download_xes_log start session=" + str(session) + " process=" + str(process))

    if Configuration.enable_download:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_log_visibility(user, process):
                if lh.check_user_enabled_download(user, process):
                    content = lh.get_handler_for_process_and_session(process, session).download_xes_log()
                    logging.info("download_xes_log complete session=" + str(session) + " process=" + str(
                        process) + " user=" + str(user))

                    return jsonify({"content": content.decode('utf-8')})

        return jsonify({"content": ""})


@PM4PyServices.app.route("/downloadCsvLog", methods=["GET"])
def download_csv_log():
    """
    Download the CSV log

    Returns
    ------------
    csv_log
        CSV log
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("download_csv_log start session=" + str(session) + " process=" + str(process))

    if Configuration.enable_download:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_log_visibility(user, process):
                if lh.check_user_enabled_download(user, process):
                    content = lh.get_handler_for_process_and_session(process, session).download_csv_log()
                    logging.info("download_csv_log complete session=" + str(session) + " process=" + str(
                        process) + " user=" + str(user))

                    return jsonify({"content": content})

    return jsonify({"content": ""})


@PM4PyServices.app.route("/getStartActivities", methods=["GET"])
def get_start_activities():
    """
    Gets the start activities from the log

    Returns
    ------------
    start_activities
        Dictionary of start activities
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_start_activities start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            dictio = lh.get_handler_for_process_and_session(process, session).get_start_activities()
            for entry in dictio:
                dictio[entry] = int(dictio[entry])
            list_act = sorted([(x, y) for x, y in dictio.items()], key=lambda x: x[1], reverse=True)
            logging.info(
                "get_start_activities complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify({"startActivities": list_act})

    return jsonify({"startActivities": []})


@PM4PyServices.app.route("/getEndActivities", methods=["GET"])
def get_end_activities():
    """
    Gets the end activities from the log

    Returns
    ------------
    end_activities
        Dictionary of end activities
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_end_activities start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            dictio = lh.get_handler_for_process_and_session(process, session).get_end_activities()
            for entry in dictio:
                dictio[entry] = int(dictio[entry])
            list_act = sorted([(x, y) for x, y in dictio.items()], key=lambda x: x[1], reverse=True)
            logging.info(
                "get_end_activities complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify({"endActivities": list_act})

    return jsonify({"endActivities": []})


@PM4PyServices.app.route("/getAttributesList", methods=["GET"])
def get_attributes_list():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_attributes_list start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            attributes_list = sorted(
                list(lh.get_handler_for_process_and_session(process, session).get_attributes_list()))
            logging.info(
                "get_attributes_list complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify({"attributes_list": attributes_list})

    return jsonify({"attributes_list": []})


@PM4PyServices.app.route("/getAttributeValues", methods=["GET"])
def get_attribute_values():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_attribute_values start session=" + str(session) + " process=" + str(process))

    # reads the requested attribute
    attribute_key = request.args.get('attribute_key', type=str)
    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            dictio = lh.get_handler_for_process_and_session(process, session).get_attribute_values(attribute_key)
            list_values = sorted([(x, y) for x, y in dictio.items()], key=lambda x: x[1], reverse=True)
            logging.info(
                "get_attribute_values complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify({"attributeValues": list_values})

    return jsonify({"attributeValues": []})


@PM4PyServices.app.route("/getAllPaths", methods=["GET"])
def get_all_paths():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_all_paths start session=" + str(session) + " process=" + str(process))

    # reads the requested attribute
    attribute_key = request.args.get('attribute_key', type=str)

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            dictio = lh.get_handler_for_process_and_session(process, session).get_paths(attribute_key)
            list_values = sorted([("@@".join(x), y) for x, y in dictio.items()], key=lambda x: x[1], reverse=True)
            logging.info(
                "get_all_paths complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify({"paths": list_values})

    return jsonify({"paths": []})


@PM4PyServices.app.route("/loginService", methods=["GET"])
def login_service():
    clean_expired_sessions()

    if Configuration.enable_session:
        # reads the user name
        user = request.args.get('user', type=str)
        # reads the password
        password = request.args.get('password', type=str)
        session_id = do_login(user, password)

        if session_id is not None:
            return jsonify({"status": "OK", "sessionEnabled": True, "sessionId": session_id})
        else:
            return jsonify({"status": "FAIL", "sessionEnabled": True, "sessionId": None})

    return jsonify({"status": "OK", "sessionEnabled": False, "sessionId": None})


@PM4PyServices.app.route("/checkSessionService", methods=["GET"])
def check_session_service():
    clean_expired_sessions()

    if Configuration.enable_session:
        # reads the session
        session = request.args.get('session', type=str)
        # reads the requested process name
        process = request.args.get('process', default=None, type=str)

        logging.info("check_session_service start session=" + str(session) + " process=" + str(process))

        if check_session_validity(session):
            user = get_user_from_session(session)
            is_admin = lh.check_is_admin(user)
            can_upload = lh.check_user_enabled_upload(user)
            if process is not None and not process == "null":
                log_visibility = lh.check_user_log_visibility(user, process)
                can_download = lh.check_user_enabled_download(user, process)

                logging.info("check_session_service complete session=" + str(session) + " process=" + str(
                    process) + " user=" + str(user))

                return jsonify(
                    {"status": "OK", "sessionEnabled": True, "session": session, "user": user, "is_admin": is_admin,
                     "can_upload": can_upload, "log_visibility": log_visibility, "can_download": can_download})
            logging.info(
                "check_session_service complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify(
                {"status": "OK", "sessionEnabled": True, "session": session, "user": user, "is_admin": is_admin,
                 "can_upload": can_upload})
        else:
            return jsonify({"status": "FAIL", "sessionEnabled": True})

    return jsonify(
        {"status": "OK", "sessionEnabled": False, "can_download": True, "can_upload": True, "is_admin": True})


def generate_random_string(N):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


@PM4PyServices.app.route("/uploadLog", methods=["POST"])
def upload_log():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("upload_log start session=" + str(session))

    if Configuration.enable_upload:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_enabled_upload(user):
                try:
                    filename = request.json["filename"]
                    base64_content = request.json["base64"]
                    basename = filename.split(".")[0] + "_" + generate_random_string(4)
                    extension = filename.split(".")[1]
                    base64_content = base64_content.split(";base64,")[1]
                    stru = base64.b64decode(base64_content).decode('utf-8')

                    if extension.lower() == "xes" or extension.lower() == "csv" or extension.lower() == "parquet":
                        filepath = os.path.join(Configuration.event_logs_path, basename + "." + extension)
                        F = open(filepath, "w")
                        F.write(stru)
                        F.close()

                        if Configuration.upload_as_temporary:
                            lh.manage_upload(user, basename, filepath, True)
                        else:
                            lh.manage_upload(user, basename, filepath, False)

                        logging.info("upload_log complete session=" + str(session) + " user=" + str(user))

                        return jsonify({"status": "OK"})
                except:
                    logging.error(traceback.format_exc())
                    pass

    return jsonify({"status": "FAIL"})


@PM4PyServices.app.route("/getAlignmentsVisualizations", methods=["POST"])
def get_alignments():
    """
    Get alignments visualizations

    Returns
    -------------
    dictio
        Dictionary containing the Petri net and the table
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_alignments start session=" + str(session) + " process=" + str(process))

    dictio = {}

    if Configuration.overall_enable_alignments:
        if check_session_validity(session):
            user = get_user_from_session(session)
            if lh.check_user_log_visibility(user, process):
                Commons.semaphore_matplot.acquire()
                try:
                    petri_string = request.json["model"]
                    svg_on_petri, svg_table = lh.get_handler_for_process_and_session(process, session).get_alignments(
                        petri_string,
                        parameters={})
                    dictio = {"petri": svg_on_petri.decode('utf-8'), "table": svg_table.decode('utf-8')}
                except:
                    logging.error(traceback.format_exc())
                    pass

                logging.info(
                    "get_alignments complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                        user))

                Commons.semaphore_matplot.release()

    ret = jsonify(dictio)

    return ret


@PM4PyServices.app.route("/addFilter", methods=["POST"])
def add_filter():
    """
    Adds a filter to the process

    Returns
    -------------
    dictio
        Success, or not
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("add_filter start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            # reads the specific filter to add
            filter = request.json['filter']
            # reads all the filters
            all_filters = request.json['all_filters']

            parameters = {}
            parameters["force_reload"] = True

            new_handler = lh.get_handler_for_process_and_session(process, session, parameters=parameters).add_filter(
                filter, all_filters)
            lh.set_handler_for_process_and_session(process, session, new_handler)

            logging.info("add_filter start session=" + str(session) + " process=" + str(process) + " user=" + str(user))

            return jsonify({"status": "OK"})

    return jsonify({"status": "FAIL"})


@PM4PyServices.app.route("/removeFilter", methods=["POST"])
def remove_filter():
    """
    Removes a filter from the process

    Returns
    -------------
    dictio
        Success, or not
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("remove_filter start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            # reads the specific filter to add
            filter = request.json['filter']
            # reads all the filters
            all_filters = request.json['all_filters']

            parameters = {}
            parameters["force_reload"] = True

            new_handler = lh.get_handler_for_process_and_session(process, session, parameters=parameters).remove_filter(
                filter, all_filters)
            lh.set_handler_for_process_and_session(process, session, new_handler)

            logging.info(
                "remove_filter complete session=" + str(session) + " process=" + str(process) + " user=" + str(user))

            return jsonify({"status": "OK"})

    return jsonify({"status": "FAIL"})


@PM4PyServices.app.route("/getUserEventLogVisibility", methods=["GET"])
def get_user_log_visibilities():
    clean_expired_sessions()

    user_log_vis = {}

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("get_user_log_visibilities start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                sorted_users, sorted_logs, user_log_vis = lh.get_user_eventlog_vis_down_remov()

                logging.info(
                    "get_user_log_visibilities complete session=" + str(session) + " this_user=" + str(this_user))

                return jsonify({"success": True, "sorted_users": sorted_users, "sorted_logs": sorted_logs,
                                "user_log_visibility": user_log_vis})

    return jsonify({"success": False})


@PM4PyServices.app.route("/addUserLogVisibility", methods=["GET"])
def add_user_log_visibility():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("add_user_log_visibility start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                user = request.args.get('user', type=str)
                process = request.args.get('process', type=str)

                lh.add_user_eventlog_visibility(user, process)

                logging.info("add_user_log_visibility complete session=" + str(session) + " this_user=" + str(
                    this_user) + " user=" + str(user) + " process=" + str(process))

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/removeUserLogVisibility", methods=["GET"])
def remove_user_log_visibility():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("remove_user_log_visibility start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                user = request.args.get('user', type=str)
                process = request.args.get('process', type=str)

                lh.remove_user_eventlog_visibility(user, process)

                logging.info("remove_user_log_visibility complete session=" + str(session) + " this_user=" + str(
                    this_user) + " user=" + str(user) + " process=" + str(process))

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/addUserLogDownloadable", methods=["GET"])
def add_user_log_downloadable():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("add_user_log_downloadable start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                user = request.args.get('user', type=str)
                process = request.args.get('process', type=str)

                lh.add_user_eventlog_downloadable(user, process)

                logging.info("add_user_log_downloadable complete session=" + str(session) + " this_user=" + str(
                    this_user) + " user=" + str(user) + " process=" + str(process))

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/removeUserLogDownloadable", methods=["GET"])
def remove_user_log_downloadable():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("remove_user_log_downloadable start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                user = request.args.get('user', type=str)
                process = request.args.get('process', type=str)

                lh.remove_user_eventlog_downloadable(user, process)

                logging.info("remove_user_log_downloadable complete session=" + str(session) + " this_user=" + str(
                    this_user) + " user=" + str(user) + " process=" + str(process))

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/addUserLogRemovable", methods=["GET"])
def add_user_log_removable():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("add_user_log_removable start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                user = request.args.get('user', type=str)
                process = request.args.get('process', type=str)

                lh.add_user_eventlog_removable(user, process)

                logging.info("add_user_log_removable complete session=" + str(session) + " this_user=" + str(
                    this_user) + " user=" + str(user) + " process=" + str(process))

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/removeUserLogRemovable", methods=["GET"])
def remove_user_log_removable():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    logging.info("remove_user_log_removable start session=" + str(session))

    if Configuration.overall_enable_sharing:
        if check_session_validity(session):
            this_user = get_user_from_session(session)
            is_admin = lh.check_is_admin(this_user)

            if is_admin:
                user = request.args.get('user', type=str)
                process = request.args.get('process', type=str)

                lh.remove_user_eventlog_removable(user, process)

                logging.info("remove_user_log_removable complete session=" + str(session) + " this_user=" + str(
                    this_user) + " user=" + str(user) + " process=" + str(process))

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/deleteEventLog", methods=["GET"])
def deleteEventLog():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    if Configuration.overall_enable_deletion:
        if check_session_validity(session):
            user = get_user_from_session(session)

            if lh.can_delete(user, process):
                lh.delete_log(process)

                return jsonify({"success": True})

    return jsonify({"success": False})


@PM4PyServices.app.route("/checkVersions", methods=["GET"])
def check_versions():
    clean_expired_sessions()

    logging.info("check_versions start")

    import pm4pyws
    import pm4py

    try:
        import pm4pybpmn

        logging.info("check_versions complete")

        return {"pm4py": str(pm4py.__version__), "pm4pyws": str(pm4pyws.__version__),
                "pm4pybpmn": str(pm4pybpmn.__version__), "hostname": str(socket.gethostname())}

    except:
        return {"pm4py": str(pm4py.__version__), "pm4pyws": str(pm4pyws.__version__),
                "hostname": str(socket.gethostname())}


def convert_str_to_bool(stri):
    if stri.lower() == "true":
        return True
    return False


@PM4PyServices.app.route("/rolesPrivacyAware", methods=["GET"])
def roles_privacy_aware():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    no_substitutions = request.args.get('no_substitutions', default=2, type=int)
    selective_lower_bound_applied = request.args.get('selective_lower_bound_applied', default="true", type=str)
    selective_upper_bound_applied = request.args.get('selective_upper_bound_applied', default="true", type=str)
    fixed_value = request.args.get('fixed_value', default=0, type=int)  # fixed_value, selective, frequency_based
    technique = request.args.get('technique', default='fixed_value', type=str)
    resource_aware = request.args.get('resource_aware', default="true", type=str)
    hashed_activities = request.args.get('hashed_activities', default="true", type=str)
    event_attributes2remove = request.args.get('event_attributes2remove', default="", type=str).split("@@")
    trace_attributes2remove = request.args.get('trace_attributes2remove', default="", type=str).split("@@")

    parameters = {}
    parameters["no_substitutions"] = no_substitutions
    parameters["selective_lower_bound_applied"] = convert_str_to_bool(selective_lower_bound_applied)
    parameters["selective_upper_bound_applied"] = convert_str_to_bool(selective_upper_bound_applied)
    parameters["fixed_value"] = fixed_value
    parameters["technique"] = technique
    parameters["resource_aware"] = convert_str_to_bool(resource_aware)
    parameters["hashed_activities"] = convert_str_to_bool(hashed_activities)
    parameters["event_attributes2remove"] = event_attributes2remove
    parameters["trace_attributes2remove"] = trace_attributes2remove

    if check_session_validity(session):
        logging.error("session " + str(session) + " is valid")
        this_user = get_user_from_session(session)
        is_admin = lh.check_is_admin(this_user)

        logging.error("this_user = " + str(this_user))
        logging.error("is_admin = " + str(is_admin))

        if is_admin:
            apply_privacy_aware.apply(process, lh.get_handler_for_process_and_session(process, session), lh, um, ex,
                                      parameters=parameters)

            logging.error("is_admin")

            return jsonify({"status": "OK"})

    return jsonify({"status": "FAIL"})


@PM4PyServices.app.route("/privacyConnectorMethod", methods=["GET"])
def privacy_connector_method():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    relation_depth = request.args.get('relation_depth', default="true", type=str)
    trace_length = request.args.get('trace_length', default="true", type=str)
    trace_id = request.args.get('trace_id', default="true", type=str)
    key = request.args.get('key', default="CHIAVECHIAVECHIA", type=str)


    logging.error("relation_depth "+str(relation_depth))
    logging.error("trace_length "+str(trace_length))
    logging.error("trace_id "+str(trace_id))

    parameters = {}
    parameters["relation_depth"] = convert_str_to_bool(relation_depth)
    parameters["trace_length"] = convert_str_to_bool(trace_length)
    parameters["trace_id"] = convert_str_to_bool(trace_id)
    parameters["key"] = key

    if check_session_validity(session):
        logging.error("session " + str(session) + " is valid")
        this_user = get_user_from_session(session)
        is_admin = lh.check_is_admin(this_user)

        logging.error("this_user = " + str(this_user))
        logging.error("is_admin = " + str(is_admin))

        if is_admin:
            apply_connector.apply(process, lh, parameters=parameters)

            logging.error("is_admin")

            return jsonify({"status": "OK"})

    return jsonify({"status": "FAIL"})


@PM4PyServices.app.route("/privacyTklc", methods=["GET"])
def privacy_tklc():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    #L = [parameters["L"]] if "L" in parameters else 2
    #C = [parameters["C"]] if "C" in parameters else 1
    #K = [parameters["K"]] if "K" in parameters else 10
    #K2 = [parameters["K2"]] if "K2" in parameters else 0.5
    #sensitive = parameters["sensitive"] if "sensitive" in parameters else []
    #T = [parameters["T"]] if "T" in parameters else ["minutes"]
    #bk_type = [parameters["bk_type"]] if "bk_type" in parameters else "set"

    L = request.args.get("L", type=int, default=2)
    C = request.args.get("C", type=int, default=1)
    K = request.args.get("K", type=int, default=10)
    K2 = request.args.get("K2", type=float, default=0.5)
    sensitive = request.args.get("sensitive", type=str, default="").split("@@")
    T = request.args.get("T", type=str, default="minutes")
    bk_type = request.args.get("bk_type", type=str, default="set")

    parameters = {}
    parameters["L"] = L
    parameters["C"] = C
    parameters["K"] = K
    parameters["K2"] = K2
    parameters["sensitive"] = sensitive
    parameters["T"] = T
    parameters["bk_type"] = bk_type

    if check_session_validity(session):
        logging.error("session " + str(session) + " is valid")
        this_user = get_user_from_session(session)
        is_admin = lh.check_is_admin(this_user)

        logging.error("this_user = " + str(this_user))
        logging.error("is_admin = " + str(is_admin))

        if is_admin:
            apply_tklc.apply(process, lh.get_handler_for_process_and_session(process, session), lh, um, ex,
                                      parameters=parameters)

            logging.error("is_admin")

            return jsonify({"status": "OK"})

    return jsonify({"status": "FAIL"})


@PM4PyServices.app.route("/getContent", methods=["GET"])
def get_content():
    """
    Gets the list of logs loaded into the system

    Returns
    -----------
    dictio
        JSONified dictionary that contains in the 'logs' entry the list of events logs
    """
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)

    process = request.args.get('process', type=str)

    encrypt_result = request.args.get('encrypt_result', type=str)

    frequency_threshold = request.args.get('frequency_threshold', default=0.0, type=float)
    key = request.args.get('key', default="CHIAVECHIAVECHIA", type=str)

    logging.error("XXXX")
    logging.error(encrypt_result)
    logging.error(frequency_threshold)

    encrypt_result = convert_str_to_bool(encrypt_result)

    logging.error("encrypt_result "+str(encrypt_result))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            ext, base64, xml = lh.get_handler_for_process_and_session(process, session).get_content(lh.get_handlers()[process], encrypt_result=encrypt_result, frequency_threshold=frequency_threshold, key=key)
            dictio = {"base64": base64.decode('utf-8'), "xml": xml.decode('utf-8'), "ext": ext}
            return jsonify(dictio)

    return jsonify({})


@PM4PyServices.app.route("/getTraceAttributes", methods=["GET"])
def get_trace_attributes_list():
    clean_expired_sessions()

    # reads the session
    session = request.args.get('session', type=str)
    # reads the requested process name
    process = request.args.get('process', default='receipt', type=str)

    logging.info("get_attributes_list start session=" + str(session) + " process=" + str(process))

    if check_session_validity(session):
        user = get_user_from_session(session)
        if lh.check_user_log_visibility(user, process):
            attributes_list = sorted(
                list(lh.get_handler_for_process_and_session(process, session).get_trace_attributes()))
            logging.info(
                "get_attributes_list complete session=" + str(session) + " process=" + str(process) + " user=" + str(
                    user))

            return jsonify({"attributes_list": attributes_list})

    return jsonify({"attributes_list": []})
