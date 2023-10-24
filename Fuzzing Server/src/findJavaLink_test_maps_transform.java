import javaLink.JavaLinkFound;

import java.util.ArrayList;

public class findJavaLink_test_maps_transform {
    public static void main(String[] args){
        //android.accounts.AbstractAccountAuthenticator$Transport: void addAccount(android.accounts.IAccountAuthenticatorResponse,java.lang.String,java.lang.String,java.lang.String[],android.os.Bundle)
//        String mainClassStrLast = "AbstractAccountAuthenticator$Transport";
//        String mainClassStr = "android.accounts." + mainClassStrLast;
        String mainClassStrLast = args[0];
        System.out.println(mainClassStrLast);
        String mainClassStr = args[1] + mainClassStrLast;
        System.out.println(mainClassStr);
//    ArrayList<String> starts_call = new ArrayList<String>();
//    starts_call.add("addAccount(");
        ArrayList<String> supportClassList = new ArrayList<String>();
//    String isMatched = "android.accounts.AbstractAccountAuthenticator$Transport: void addAccount(android.accounts.IAccountAuthenticatorResponse,java.lang.String,java.lang.String,java.lang.String[],android.os.Bundle)";
        String isMatched = args[2];
        System.out.println(isMatched);
        //com.android.server.appwidget.AppWidgetServiceImpl: android.widget.RemoteViews getAppWidgetViews(java.lang.String,int)
        mainClassStrLast = "AppWidgetServiceImpl";
        mainClassStr = "com.android.server.appwidget." + mainClassStrLast;
        isMatched = "com.android.server.appwidget.AppWidgetServiceImpl: android.widget.RemoteViews getAppWidgetViews(java.lang.String,int)";
        JavaLinkFound.run(mainClassStrLast, mainClassStr, 1, isMatched, supportClassList);
    }
}
