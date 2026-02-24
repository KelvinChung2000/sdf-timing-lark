// Minimal cell library matching spec-example1.sdf cell types

module INV(input i, output z);
    assign z = ~i;
endmodule

module OR2(input i1, input i2, output z);
    assign z = i1 | i2;
endmodule

module AND2(input i1, input i2, output z);
    assign z = i1 & i2;
endmodule
