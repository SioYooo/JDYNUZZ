import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;

// 实现了一个 Server 类，用来接收从 client 传回的数据
public class Server {

    public static final int SERVER_PORT = 6100;
    private ServerSocket serverSocket;
    private boolean isRunning;

    public Server() throws IOException {
        InetAddress ia = InetAddress.getByName("127.0.0.1");
        serverSocket = new ServerSocket(SERVER_PORT, 1, ia);
        isRunning = true;
        System.out.println("Server started on " + ia + ":" + SERVER_PORT);
    }

    public void start() {
        while (isRunning) {
            try {
                Socket clientSocket = serverSocket.accept();
                handleClient(clientSocket);
            } catch (IOException e) {
                System.out.println("Error accepting client connection: " + e.getMessage());
            }
        }
    }

    private void handleClient(Socket clientSocket) {
        new Thread(() -> {
            try {
                String clientAddress = clientSocket.getInetAddress().getHostAddress();
                System.out.println("New connection from " + clientAddress);

                BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
                PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);

                String message;
                while ((message = in.readLine()) != null) {
                    System.out.println("Message from " + clientAddress + ": " + message);
                    out.println("Echo: " + message);
                }

                clientSocket.close();
                System.out.println("Connection with " + clientAddress + " closed");
            } catch (IOException e) {
                System.out.println("Error handling client: " + e.getMessage());
            }
        }).start();
    }

    public void stop() throws IOException {
        isRunning = false;
        serverSocket.close();
        System.out.println("Server stopped");
    }
}
