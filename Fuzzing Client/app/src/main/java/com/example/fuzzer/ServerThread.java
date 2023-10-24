package com.example.fuzzer;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.List;

class ServerThread{
    private BufferedReader reader;
    private ServerSocket serverSocket;
    private Socket socket;
    /**
     * 创建服务端的程序，读取客户端传来的数据
     */
    void getserver(){
        try {
            serverSocket = new ServerSocket(7100);		//实例化服务端socket
            System.out.println("服务器套接字已经创建成功");
            while (true) {
                System.out.println("等待客户机的连接:");
                socket = serverSocket.accept();        //实例化socket对象
                reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));	//实例化BufferReader对象
                getClientMessage();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    private void getClientMessage() {
        try {
            while (true) {
                System.out.println("客户机传来的信息是："+reader.readLine());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}