package util;

import java.util.List;

public class JniPath {
    public JniPath(List<String> path) {
        this.path = path;
    }

    public List<String> getPath() {
        return path;
    }

    public void setPath(List<String> path) {
        this.path = path;
    }

    private List<String> path;
}
