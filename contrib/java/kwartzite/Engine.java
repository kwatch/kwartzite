package kwartzite;

import java.io.File;
import java.io.InputStream;
import java.io.FileInputStream;
//import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Map;

public class Engine {

    private ClassLoader _class_loader;

    public ClassLoader getClassLoader() { return _class_loader; }
    public void setClassLoader(ClassLoader loader) { _class_loader = loader; }

    public Engine() {
        this((String)null);
    }

    public Engine(String directory) {
        _class_loader = new KlassLoader(directory);
    }

    public Engine(ClassLoader loader) {
        _class_loader = loader;
    }

    public kwartzite.Renderable getRenderableObject(String classname) {
        try {
            //System.err.println("*** debug: _class_loader="+_class_loader.toString());
            Class klass = Class.forName(classname, true, _class_loader);
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
        String output = engine.render("stocks.indexHtml", context);
        System.out.print(output);
    }

}