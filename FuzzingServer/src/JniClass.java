import java.util.List;

    public class JniClass {
        private String class_;
        private List<String> return_;
        private String fun;
        private List<String> parameters;
        private boolean static_;

        public JniClass(String class_, List<String> return_, String fun, List<String> parameters, boolean static_) {
            this.class_ = class_;
            this.return_ = return_;
            this.fun = fun;
            this.parameters = parameters;
            this.static_ = static_;
        }

        public String getClass_() {
            return class_;
        }

        public void setClass_(String class_) {
            this.class_ = class_;
        }

        public List<String> getReturn_() {
            return return_;
        }

        public void setReturn_(List<String> return_) {
            this.return_ = return_;
        }

        public String getFun() {
            return fun;
        }

        public void setFun(String fun) {
            this.fun = fun;
        }

        public List<String> getParameters() {
            return parameters;
        }

        public void setParameters(List<String> parameters) {
            this.parameters = parameters;
        }

        public boolean getStatic_() {
            return static_;
        }

        public void setStatic_(boolean static_) {
            this.static_ = static_;
        }

        public String fullName(){
            String par = "";
            for(String p : parameters){
                par += p + ", ";
            }
            par = par.substring(0, par.length() - 2);
            return class_ + " " + return_.get(0) + " " + fun + "(" + par + ")";
        }

        public void print(){
            System.out.println(class_ + " " + return_ + " " + fun + "(" + parameters + ")");
        }
    }

