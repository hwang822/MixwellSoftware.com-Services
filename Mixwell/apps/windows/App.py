# pip install kivy-garden
# pip install Cefpython3==66.0
#https://www.youtube.com/watch?v=8MkTblYSYC0&t=2s
#Python: Kivy WebView Android .apk File Format Full Video

import webview

webview.create_window(
    "Mixwell Services",
    "https://www.mixwellsoftware.com"
)

webview.start()
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from jnius import autoclass


#from kivy_garden.webview import WebView

class MyApp(App):
    def build(self):
        layout = BoxLayout()
        #webview = WebView(url="https://example.com")
        #layout.add_widget(webview)
        return layout

class WebViewApp(App):
    def build(self):
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        WebView = autoclass('android.webkit.WebView')
        webview = WebView(activity)
        webview.getSettings().setJavaScriptEnabled(True)
        webview.loadUrl("https://www.mixwellsoftware.com")
        activity.setContentView(webview)
        return Widget()

if __name__ == "__main__":
##    MyApp().run()
    WebViewApp(app)
"""