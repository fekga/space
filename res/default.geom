#version 330 core
layout(triangles) in;
layout (triangle_strip, max_vertices=3) out;

in vec3 gPosition[3];

void main()
{
    for(int i = 0; i < gl_in.length(); ++i)
    {
        gl_Position = vec4(gPosition[i],1);
        EmitVertex();
    }
    EndPrimitive();
}