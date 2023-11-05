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
    InetAddress ia;
    public Server() throws Exception {
        if (addr != null && !addr.isEmpty()) {
            ia = InetAddress.getByName(addr);  //ipAddress);
            System.out.println("18 MSS InetAddress.getByName(" + addr + ") = " + ia);
            try {
                server = new ServerSocket(port, 1, ia);
                System.out.println("20 MSS Nonempty ipAddress: instantiated ServerSocket");
            } catch( IOException e) {
                System.out.println("22 MSS while instantiating ServerSocket: " + e);
            }
        }
        else {
            ia = InetAddress.getLocalHost();
            server = new ServerSocket(port, 1, ia);
            System.out.print("28 MSS empty ipAddress: MSS new ServerSocket port ");
            System.out.print(port);
            System.out.println(", addr " + ia);
        }
    }

    public void listen() throws Exception {
        String data = null;
        Socket client = server.accept();  //Hangs here
        String clientAddress = client.getInetAddress().getHostAddress();
        System.out.println("35 MSS New connection from " + clientAddress);

        BufferedReader in = new BufferedReader(
                new InputStreamReader(client.getInputStream()));
        while ( (data = in.readLine()) != null ) {
            System.out.println("40 MSS Message from " + clientAddress + ": " + data);
        }
    }

}
