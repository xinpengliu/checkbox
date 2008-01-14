import os.path, sys
import gtk, gtk.glade

from hwtest.lib.environ import add_variable, remove_variable
from hwtest.user_interface import UserInterface


class GTKInterface(UserInterface):

    def __init__(self, config):
        super(GTKInterface, self).__init__(config)

        # load UI
        gtk.window_set_default_icon_name("hwtest")
        gtk.glade.textdomain(self.gettext_domain)
        self.widgets = gtk.glade.XML(os.path.join(config.gtk_path,
            "hwtest-gtk.glade"))
        self.widgets.signal_autoconnect(self)

        self._dialog = self._get_widget("dialog_hwtest")
        self._dialog.set_title(config.title)

        self._notebook = self._get_widget("notebook_hwtest")

    def _get_widget(self, widget):
        return self.widgets.get_widget(widget)

    def _get_radiobutton(self, map):
        for radiobutton, value in map.items():
            if self._get_widget(radiobutton).get_active():
                return value
        raise Exception, "failed to map radiobutton"

    def _set_label(self, name, text):
        label = self._get_widget(name)
        label.set_text(text)

    def _get_textview(self, name):
        textview = self._get_widget(name)
        buffer = textview.get_buffer()
        data = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        return data

    def _set_textview(self, name, data):
        buffer = gtk.TextBuffer()
        buffer.set_text(data)
        textview = self._get_widget(name)
        textview.set_buffer(buffer)

    def _set_sensitive(self, name, boolean):
        widget = self._get_widget(name)
        widget.set_sensitive(bool(boolean))

    def _run_dialog(self):
        response = self._dialog.run()
        while gtk.events_pending():
            gtk.main_iteration(False)

        return response

    def _run_question(self, question):
        question.run()
        self._set_label("label_question", question.description)

    def show_wait(self, message=None):
        self._set_sensitive("button_previous", False)
        self._set_sensitive("button_next", False)

        self._set_label("label_wait", message)
        self._get_widget("progressbar_wait").set_fraction(0)
        self._notebook.set_current_page(3)

        self._dialog.show()

    def show_pulse(self):
        self._get_widget("progressbar_wait").pulse()
        while gtk.events_pending():
            gtk.main_iteration(False)

    def show_intro(self):
        # Set buttons
        self._set_sensitive("button_previous", False)
        self._set_sensitive("button_next", True)
        self._notebook.set_current_page(0)

        self._run_dialog()

    def show_category(self):
        # Set buttons
        self._set_sensitive("button_previous", False)
        self._set_sensitive("button_next", True)
        self._notebook.set_current_page(1)

        self._run_dialog()

        return self._get_radiobutton({
            "radiobutton_desktop": "desktop",
            "radiobutton_laptop": "laptop",
            "radiobutton_server": "server"})

    def show_question(self, question, has_prev=True, has_next=True):
        # Set buttons
        self._set_sensitive("button_test_again", question.command)
        self._set_sensitive("button_previous", has_prev)
        self._set_sensitive("button_next", has_next)
        self._get_widget("button_previous").show()
        self._notebook.set_current_page(2)

        # Set test again button
        button_test_again = self._get_widget("button_test_again")
        if hasattr(self, "handler_id"):
            button_test_again.disconnect(self.handler_id)
        self.handler_id = button_test_again.connect("clicked",
            lambda w, question=question: self._run_question(question))

        # Default answers
        if question.answer:
            answer = question.answer
            self._set_textview("textview_comment", answer.data)
            self._get_widget("radiobutton_%s" % answer.status).set_active(True)
        else:
            self._set_textview("textview_comment", "")
            self._get_widget("radiobutton_skip").set_active(True)

        self._run_question(question)
        response = self._run_dialog()

        status = self._get_radiobutton({
            "radiobutton_yes": "yes",
            "radiobutton_no": "no",
            "radiobutton_skip": "skip"})
        data = self._get_textview("textview_comment")
        question.set_answer(status, data)

        return response

    def show_exchange(self, message=None, error=None):
        self._set_sensitive("button_previous", False)
        self._set_sensitive("button_next", True)
        self._notebook.set_current_page(4)

        if message is not None:
            self._get_widget("label_exchange").set_markup(message)

        if error is not None:
            markup= "<span color='#FF0000'><b>%s</b></span>" % error
            self._get_widget("label_exchange_error").set_markup(markup)

        response = self._run_dialog()
        authentication = self._get_widget("entry_authentication").get_text()

        return authentication

    def show_final(self, message=None):
        self._set_sensitive("button_previous", False)
        self._set_sensitive("button_next", True)
        self._notebook.set_current_page(5)

        if message is not None:
            self._get_widget("label_final").set_markup(message)

        response = self._run_dialog()

        return response

    def show_error(self, title, text):
        md = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_CLOSE, message_format=text)
        md.set_title(title)
        md.run()
        md.hide()
        while gtk.events_pending():
            gtk.main_iteration(False)

    def on_dialog_hwtest_delete(self, widget, event=None):
        sys.exit(0)
        return True
