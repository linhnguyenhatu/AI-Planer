from flask import Flask, render_template, request,session
from codefest import  griffin_travelplanner

app = Flask(__name__)
app.secret_key = 'your_secret_key'
dialog = ""
text_input = ""
#dashboard
@app.route('/', methods=['GET', 'POST'])
def dashboard():
    global dialog
    global text_input
    text_input = request.form.get("input-bar")
    if request.method == 'POST':
      if request.form.get('button_action') == 'activated':
          text_input = request.form.get("input-bar")
          dialog = griffin_travelplanner(text_input)
          
    return render_template('dashboard.html',key_change = key_change, dialog = dialog, text_input = text_input)

def key_change(str):
    list1 = str.split("_")
    result = ""
    for i in range (0, len(list1)):
        result += list1[i] + " "
    a = list(result)
    a[0] = a[0].upper()
    return ("".join(a))

if __name__ == '__main__':
    app.run(debug=True)
