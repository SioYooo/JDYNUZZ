import java.io.PrintWriter;
import java.net.Socket;
/**
 *   作用：一直接收服务端转发过来的信息
 * */
public class Client extends Thread {
    private PrintWriter printWriter;
    Socket socket;
    /**
     * 创建的Tcp客户端程序
     */


    public void connect() {
        try {
            socket = new Socket("127.0.0.1",6100);
            printWriter = new PrintWriter(socket.getOutputStream(),true);   //将printwriter中的信息流写入到套接字的输出流传送给服务端
            printWriter.close();
            socket.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
