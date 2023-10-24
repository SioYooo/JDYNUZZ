package util;

public class ApiDependency {
    private String A;
    private String B;

    public String getA() {
        return A;
    }

    public void setA(String a) {
        A = a;
    }

    public String getB() {
        return B;
    }

    public void setB(String b) {
        B = b;
    }

    public ApiDependency(String a, String b) {
        A = a;
        B = b;
    }
}
