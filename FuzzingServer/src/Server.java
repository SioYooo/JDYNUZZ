import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;

public class Server {

    public static ServerSocket server;

    public static String addr = "127.0.0.1";
    public static int port = 6100;

    public Server() throws Exception {
        server = new ServerSocket(port, 50, InetAddress.getByName(addr));
        System.out.println("Server started");
        System.out.println("Waiting for a client ...");
    }

}
