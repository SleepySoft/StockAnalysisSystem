from flask import Flask

app = Flask(__name__)  # 创建一个实例


@app.route('/')
def hello_world():
    return 'hello world'


if __name__ == '__main__':
    app.run(debug=True)


