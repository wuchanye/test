# 使用Python映像
FROM python:3.7

# 设置工作目录
WORKDIR /app

# 安装所需的系统依赖库（例如，Xvfb和字体库）
RUN apt-get update && apt-get install -y xvfb fonts-liberation

# 安装Python依赖项
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# 复制应用程序代码到容器中
COPY . /app

# 设置Chrome和ChromeDriver的路径
# ENV CHROME_BINARY /usr/bin/chromium
# ENV CHROMEDRIVER_PATH /usr/local/bin/chromedriver

# 暴露一个端口，如果需要的话
EXPOSE 5000

# 启动你的Python应用程序
CMD ["python", "app.py"]
