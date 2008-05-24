package kwartzite;

import java.io.File;
import java.io.IOException;
import kwartzite.util.FileUtil;

public class KlassLoader extends ClassLoader {

    private String _dir;

    public KlassLoader(String dir) {
        _dir = dir;
    }
    public KlassLoader() {
        _dir = null;
    }

    public String getDirectory() { return _dir; }
    public void setDirectory(String dir) { _dir = dir; }

    //@Override
    //public Class<?> loadClass(String name) throws ClassNotFoundException {
    //    System.err.println("*** debug: loadClass(): name='"+name);
    //    //return super.loadClass(name);
    //    return loadClass(name, true);
    //}
    //
    //@Override
    //protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
    //    System.err.println("*** debug: loadClass(): name='"+name+"', resolve="+resolve);
    //    return super.loadClass(name, resolve);
    //}

    @Override
    protected Class<?> findClass(String classname) throws ClassNotFoundException {
        //System.err.println("***! debug: findClass(): classname='"+classname+"'");
        String filename = classname.replace('.', File.separatorChar) + ".class";
        File file = _dir == null ? new File(filename) : new File(_dir, filename);
        byte[] binary = null;
        try {
            binary = FileUtil.readBinaryFile(file);
            //System.out.println("*** debug: '" + filename + "': class found.");
        } catch (IOException ex) {
            //System.out.println("*** debug: '" + classname + "': class not found.");
            super.findClass(classname);
            //throw new ClassNotFoundException(classname, ex);
        }
        return defineClass(classname, binary, 0, binary.length);
    }

}
