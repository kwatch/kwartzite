package kwartzite;

import java.io.File;
import java.io.InputStream;
import java.io.FileInputStream;
//import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Map;

public class Engine {

    public static class KlassLoader extends ClassLoader {
        static final int BUF_SIZE = 4096;  // 4KB
        private String _dir;

        public KlassLoader(String dir) {
            _dir = dir;
        }
        public KlassLoader() {
            _dir = null;
        }

        public String getDirectory() { return _dir; }
        public void setDirectory(String dir) { _dir = dir; }

        @Override
        protected Class findClass(String classname) throws ClassNotFoundException {
            String filename = classname.replace('.', File.separatorChar) + ".class";
            File file = _dir == null ? new File(filename) : new File(_dir, filename);
            byte[] binary = null;
            try {
                binary = _readBinaryFile(file);
                System.out.println("*** deubug: class found: " + filename);
            } catch (IOException ex) {
                System.out.println("*** deubug: class not found: classname");
                super.findClass(classname);
                //throw new ClassNotFoundException(classname, ex);
            }
            return defineClass(classname, binary, 0, binary.length);
        }

        private static byte[] _readBinaryFile(File file) throws IOException {
            InputStream in = null;
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[BUF_SIZE];
            try {
                in = new FileInputStream(file);
                //in = new BufferedInputStream(new FileInputStream(file), BUF_SIZE);
                int n;
                while ((n = in.read(buf, 0, BUF_SIZE)) >= 0) {
                    out.write(buf, 0, n);
                }
            } finally {
                if (in != null) in.close();
            }
            return out.toByteArray();
        }

    }


    private String _directory;
    private KlassLoader _loader = new KlassLoader();
    private boolean _debug_mode = true;

    public String getDirectory() { return _directory; }
    public void setDirectory(String directory) {
        _directory = directory;
        _loader.setDirectory(directory);
    }
    public boolean isDebugMode() { return _debug_mode; }
    public void setDebugMode(boolean debug_mode) { _debug_mode = debug_mode; }

    public Engine() {
        this(null);
    }

    public Engine(String directory) {
        setDirectory(directory);
    }

    public kwartzite.Renderable getRenderableObject(String classname) {
        ClassLoader loader = _debug_mode ? new KlassLoader(_directory) : _loader;
        try {
            Class klass = Class.forName(classname, true, loader);
            Object obj = klass.newInstance();
            if (! (obj instanceof kwartzite.Renderable)) {
                throw new IllegalArgumentException(classname + ": should implement kwartzite.Renderable.");
            }
            return (kwartzite.Renderable)obj;
        }
        catch (ClassNotFoundException ex) {
            throw new RuntimeException(ex);
        }
        catch (InstantiationException ex) {
            throw new RuntimeException(ex);
        }
        catch (IllegalAccessException ex) {
            throw new RuntimeException(ex);
        }
    }

    public String render(String classname, Map<String, Object> context) {
        kwartzite.Renderable page = getRenderableObject(classname);
        String output = page.render(context);
        return output;
    }


    public static void main(String[] args) throws Exception {
        // create context object
        java.util.Map<String, Object> context = new java.util.HashMap<String, Object>();
        context.put("title", "Kwartzite Example");
        java.util.List<Object> list = new java.util.ArrayList<Object>();
        list.add("<AAA>"); list.add("B&B"); list.add("\"CCC\"");
        context.put("list", list);
        // render template
        Engine engine = new Engine("views");
        String output = engine.render("hello.ExampleHtml", context);
        System.out.print(output);
    }

}