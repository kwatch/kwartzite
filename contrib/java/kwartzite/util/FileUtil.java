package kwartzite.util;

import java.io.*;

public class FileUtil {

    static int BUF_SIZE = 4096; // 4KB

    public static byte[] readBinaryFile(File file) throws IOException {
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