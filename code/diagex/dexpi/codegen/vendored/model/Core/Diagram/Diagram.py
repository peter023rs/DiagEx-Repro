Core = MODEL(name='Core')
DATA_TYPES = Core.DataTypes

DIAGRAM = Core.Diagram = PACKAGE(
    description=r'''
        Two-dimensional engineering diagrams.    
    
        The <!SELF> package provides concepts
        
        1. for the graphical representation of a :sp:element:`~Core.ConceptualObject`,
        
        2. for linking parts of this graphical representation to parts of the
           :sp:element:`~!Core.ConceptualObject`, and
        
        3. for semantic annotations of the graphical representation.


        .. admonition:: technical
        
           This specification is not a drawing standard. It does not prescribe any drawing style or
           standard and it does not prescribe which information in a
           :sp:element:`~!Core.ConceptualObject` has to be represented in a <SELF.Diagram>.

        .. admonition:: technical
        
           Until version 1.2, graphics has not been in the scope of the DEXPI P&ID Specification.
           Graphics was handled as prescribed by :ref:`standard-proteus`. Over the years, some best
           practices concerning graphics have evolved in the DEXPI community, and fragmentary
           annotations have been added to the DEXPI P&ID Specification.
           
           In DEXPI P&ID Specification 1.3, an informative Graphics package was added to cover
           conceptual and graphics information in a single comprehensive model.
           
           For the P&ID Specification 1.4, the Graphics package was further
           elaborated, and it is now a normative part of the specification. It serves to document
           the best practices that have emerged in the past, but no new features have been added.  
           
           The Graphics package is independent from Proteus Schema in the sense that it is a pure
           UML package. But, like for all other packages in this specification, mappings to Proteus
           Schema are defined that describe how instances of the package's types are serialized.
           In consequence, the features of the Graphics package are constrained to what is supported
           by Proteus Schema. Future versions of the DEXPI P&ID Specification will skip support for
           Proteus Schema, such that additional features can be added to the Graphics package
           depending on the DEXPI community's needs.
           
           Since DEXPI 2.0, the Graphics package can be used for both P&IDs and process models.
        
        
        Example
        -------

           
        We consider a simple :sp:element:`~Core.ConceptualModel` :sp:name:`cm` that contains a
        single :sp:element:`~Plant.ProcessEquipment.CentrifugalPump` with two
        :sp:element:`ProcessNozzles <Plant.ProcessEquipment.ProcessNozzle>` and a
        :sp:element:`~Plant.ProcessEquipment.Chamber`; in total, there are five
        :sp:element:`ConceptualObjects <Core.ConceptualObject>`:
        
        .. image:: example1.*
        
        A typical graphical representation of this model may look like this:
        
        .. image:: exampleDiagram.*
        
        Linking Graphics and Conceptual Objects
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        The graphics can be decomposed in parts each of which represents one of the
        :sp:element:`ConceptualObjects <Core.ConceptualObject>`. For each of these parts, we use a
        <SELF.RepresentationGroup>:
        
        .. image:: example2.*
        
        - The <SELF.Diagram> :sp:name:`d` represents the entire :sp:element:`~Core.ConceptualModel`.
          <!SELF.Diagram> is a subclass of <SELF.RepresentationGroup> that is meant to be used for
          the entire graphics. In addition to a conventional <SELF.RepresentationGroup>, a
          <SELF.Diagram> has a size (width and height) and a background color.
        
        - :sp:name:`cp_grp` is the <SELF.RepresentationGroup> for the
          :sp:element:`~Plant.ProcessEquipment.CentrifugalPump` :sp:name:`cp`.
        
        - :sp:name:`pn1_grp` and :sp:name:`pn2_grp` represent the two
          :sp:element:`ProcessNozzles <Plant.ProcessEquipment.ProcessNozzle>` :sp:name:`pn1` and
          :sp:name:`pn2`.
        
        Note that the composition hierarchy of the <!SELF.Diagram> corresponds exactly to the
        composition hierarchy of the :sp:element:`~Core.ConceptualModel`. In the
        :sp:element:`~Core.ConceptualModel`, :sp:name:`pn1` is a component of :sp:name:`cp`, and in
        the <!SELF.Diagram>, :sp:name:`pn1_grp` is a component of :sp:name:`cp_grp`.
        
        However, if a :sp:element:`~Core.ConceptualObject` (including all its descendants) has no
        graphical representation at all, no <SELF.RepresentationGroup> is required: In the example
        above, there is no <SELF.RepresentationGroup> for the :sp:element:`~Plant.ProcessEquipment.Chamber`
        :sp:name:`ch`. 
        
        Adding Semantics
        ~~~~~~~~~~~~~~~~
        
        So far, we have decomposed the overall graphics in
        :sp:element:`RepresentationGroups <Core.Diagram.RepresentationGroup>` that correspond to
        certain :sp:element:`ConceptualObjects <Core.ConceptualObject>`. On a finer level of
        granularity, we can identify parts with different meanings. These meanings are covered by
        different subclasses of the abstract class <SELF.RepresentationTypeGroup>. In the example,
        two of these subclasses are used: <SELF.Static> and
        :sp:element:`~Plant.Diagram.EquipmentTagNameLabel`.
        
        .. image:: example3.*
        
        - Consider :sp:name:`cp_grp`, the <SELF.RepresentationGroup> of the 
          :sp:element:`~Plant.ProcessEquipment.CentrifugalPump` :sp:name:`cp`. In addition to the two
          groups for the :sp:element:`ProcessNozzles <Plant.ProcessEquipment.ProcessNozzle>`,
          :sp:name:`cp_grp` now contains two
          :sp:element:`RepresentationTypeGroups <Core.Diagram.RepresentationTypeGroup>`.
        
          - The <SELF.Static> group contains the actual
            :sp:element:`~Plant.ProcessEquipment.CentrifugalPump` graphics without any annotations, labels,
            etc.
          
          - The :sp:element:`~Plant.Diagram.EquipmentTagNameLabel` group displays the tag name of
            the :sp:element:`~Plant.ProcessEquipment.CentrifugalPump`.
          
        - :sp:name:`pn1_grp` contains a <SELF.Static> group for the basic symbol of the
          :sp:element:`~Plant.ProcessEquipment.ProcessNozzle`.
        
        - :sp:name:`pn2_grp` contains another <SELF.Static> group for the second
          :sp:element:`~Plant.ProcessEquipment.ProcessNozzle` symbol.
        
        Whereas :sp:element:`RepresentationGroups <Core.Diagram.RepresentationGroup>` can be
        decomposed in further groups,
        :sp:element:`RepresentationTypeGroups <Core.Diagram.RepresentationTypeGroup>` cannot contain
        further groups.
        
        
        Adding Graphical Elements
        ~~~~~~~~~~~~~~~~~~~~~~~~~
        
        :sp:element:`RepresentationTypeGroups <Core.Diagram.RepresentationTypeGroup>` rather contain
        :sp:element:`GraphicalElements <Core.Diagram.GraphicalElement>` such as geometric
        primitives, texts, or :sp:element:`ShapeUsages <Core.Diagram.ShapeUsage>`.
        
        .. image:: example4.*
        
        - The <SELF.Static> group for the :sp:element:`~Plant.ProcessEquipment.CentrifugalPump` contains a
          <SELF.ShapeUsage>, i.e., a reference to a reusable <SELF.Shape> with information about
          this specific usage (scaling, rotation, position).
        
        - The :sp:element:`~Plant.Diagram.EquipmentTagNameLabel` for the
          :sp:element:`~Plant.ProcessEquipment.CentrifugalPump` contains a <SELF.Text>.
        
        - Both <SELF.Static> groups for the two
          :sp:element:`ProcessNozzles <Plant.ProcessEquipment.ProcessNozzle>` contain a <SELF.ShapeUsage>.
        
        
        Coordinate System
        -----------------
        
        The coordinate system used is a 2D Cartesian system whose horizontal axis is oriented to the right and whose vertical axis is oriented to the bottom. In consequence, angles are measured clockwise.
        
        Lengths are dimensionless. In the examples, we assume they are in millimeters.
        
        
        .. admonition:: proteus
        
        In Proteus Schema, the vertical axis to the top, and angles are measured anti-clockwise.

        
        Mapping to SVG
        --------------
        
        The purpose of these mappings is to define the visualization of instances of the types in
        this package, i.e., "how they look like".
        
        In order to keep the mappings simple, the SVG mappings for all
        :sp:element:`GraphicalPrimitives <Core.Diagram.GraphicalPrimitive>` are defined such that
        they can be easily scaled when they appear in a <SELF.Shape> (in particular, they use
        ``vector-effect = "non-scaling-stroke"``). In consequence, further scaling, e.g., in an
        application, will lead to unacceptable results.
        
        .. admonition:: technical
        
        The SVG mappings in this specification must not be misunderstood as a proposal for
        exchanging P&ID graphics via SVG.
        

        .. _modulo-operator:
        
        Modulo Operator
        ---------------
        
        In some calculations for the SVG and Proteus mappings, the *modulo operator* (or *remainder
        of division*) is used. As the modulo operator can be defined in different ways, we give a
        definition of how the operator is used in this specification. We content ourselves with a
        definition for positive quotients.
        
        Let :math:`q > 0, a \in \mathbb R`. Then
        
        .. math::
        
           a\,\textrm{mod}\,q = a - \left\lfloor \frac a q \right\rfloor \cdot q \quad .
        
        :math:`\lfloor.\rfloor` is the *floor function* that for :math:`x \in \mathbb R` yields the largest integer :math:`n` such that :math:`n \leq x`.
        
        For example,
        
        .. math::
        
           0\,\textrm{mod}\,360 &= 0 - \left\lfloor \frac {0} {360} \right\rfloor \cdot 360 = 0 - 0 \cdot 360 = 0 \quad, \\
           100\,\textrm{mod}\,360 &= 100 - \left\lfloor \frac {100} {360} \right\rfloor \cdot 360 = 100 - 0 \cdot 360 = 100 \quad, \\
           359\,\textrm{mod}\,360 &= 359 - \left\lfloor \frac {359} {360} \right\rfloor \cdot 360 = 359 - 0 \cdot 360 = 359 \quad, \\
           360\,\textrm{mod}\,360 &= 360 - \left\lfloor \frac {360} {360} \right\rfloor \cdot 360 = 360 - 1 \cdot 360 = 0 \quad, \\
           (-100)\,\textrm{mod}\,360 &= -100 - \left\lfloor \frac {-100} {360} \right\rfloor \cdot 360 = -100 - (-1) \cdot 360 = 260 \quad. \\
           
        .. admonition:: technical
        
           The definition of the modulo operator differs between programming languages. For example, the modulo operator in Python, written :code:`%`, coincides with the definition above. The modulo operator in JavaScript (ECMAScript), also written :code:`%`, behaves differently for negative dividends: :code:`-100 % 360` is evaluated to :code:`-100`.
    ''')



##############
#   Data Types
##############

DIAGRAM.Color = AGGREGATED_DATA_TYPE(
    description=r'''
        A color.
        
        <!SELF> is based on the RGB color model (e.g., see 
        `Wikipedia <https://en.wikipedia.org/wiki/RGB_color_spaces>`__ for an
        overview). For each channel *red*, *green*, and *blue*, <!SELF> has an attribute <SELF.R>,
        <SELF.G>, and <SELF.B> that gives the intensity of the channel. Intensities are given as
        values of :sp:element:`~Core.DataTypes.UnsignedByte`, i.e., integers in the range [0, 255].
        ''',
    details=r'''
        Simplified Literals
        -------------------
        
        Within this specification, we use the hexadecimal SVG representation of 
        a :sp:element:`~Core.Diagram.Color` (without the string delimiters) as a convenient literal
        to refer to that :sp:element:`~Core.Diagram.Color`. 
        
        For example, :code:`#0000ff` refers to the :sp:element:`<Core.Diagram.Color>` *blue* with
        :code:`R=0`, :code:`G=0`, and :code:`B=255`.
         
        Mapping to SVG
        --------------
        
        There are several syntactical variants to map a :sp:element:`~Core.Diagram.Color` to SVG. Here, we 
        use the `RGB Hexadecimal Notation <https://www.w3.org/TR/css-color-4/#hex-notation>`__ 
        with 6 digits as defined by :ref:`standard-css-color-4`. It has the form
        :code:`'#RRGGBB'`, where :code:`RR`, :code:`GG`, and :code:`BB` are 2-digit
        hexadecimal representations of the integer values of the attributes <SELF.R>, <SELF.G>, and
        <SELF.B>. Conventional hexadecimal digits are used: :code:`0`, ..., :code:`9`, :code:`a`, ..., :code:`f`.
        Capitalized versions of the latter are also allowed: :code:`A`, ..., :code:`F`. To ensure 2 digits for each
        integer, a leading zero is added if required.
        
        .. admonition:: example
        
            Consider the :sp:element:`~Core.Diagram.Color` with :code:`R=0`, :code:`G=10`, and :code:`B=255`.
            
            The hexadecimal representations of the attributes are :code:`00`, :code:`0a`, and :code:`ff`. 
            
            Hence, the SVG representation of the color is :code:`'#000aff'`.

    ''')

DIAGRAM.Color.R = DATA_PROPERTY(
    description=r'''
        The intensity of the red channel of the <OWNER>.
    ''',
    type=BUILTIN.UnsignedByte,
    lower=1,
    upper=1,
    exampleValue=127)

DIAGRAM.Color.G = DATA_PROPERTY(
    description=r'''
        The intensity of the green channel of the <OWNER>.
    ''',
    type=BUILTIN.UnsignedByte,
    lower=1,
    upper=1,
    exampleValue=0)

DIAGRAM.Color.B = DATA_PROPERTY(
    description=r'''
        The intensity of the blue channel of the <OWNER>.
    ''',
    type=BUILTIN.UnsignedByte,
    lower=1,
    upper=1,
    exampleValue=255)

DIAGRAM.Point = AGGREGATED_DATA_TYPE(
    description=r'''
        A point in the X-Y-plane.
    ''')

DIAGRAM.Point.X = DATA_PROPERTY(
    description=r'''
        The X (horizontal) coordinate of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=50.5)

DIAGRAM.Point.Y = DATA_PROPERTY(
    description=r'''
        The Y (horizontal) coordinate of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=-1.2)

DIAGRAM.Stroke = AGGREGATED_DATA_TYPE(
    description=r'''
        A stroke defines the visual appearance of a line.
    ''',
    details=r'''
        Simplified Literals
        ===================
        
        Within this specification, a simplified type of literal is used
        to refer to a <SELF>. This literal is composed of
        
        - a decimal representation of the <SELF.Width>, followed 
          by :code:`mm`,
        
        - the simplified literal of the <SELF.Color> of the <SELF>
          (see :sp:element:`~Core.Diagram.Color`),
        
        - the name of the <SELF.DashStyle> of the <SELF>
          (see :sp:element:`~Core.Diagram.DashStyle`).
        
        The three components are separated by spaces.
        
        For example, a <SELF> with 
        
        - <SELF.Width> = :code:`2`,
        
        - <SELF.Color> = :code:`#00ff00`, and
        
        - <SELF.DashStyle> = :sp:element:`~Core.Diagram.DashStyle.Dot`
        
        is represented as :code:`2mm #00ff00 Dot`.
        

        Mapping to SVG
        ==============
        
        A <SELF> is mapped to a set of XML attributes, which are added to the SVG
        element (e.g., a 
        `svg:polygon <https://www.w3.org/TR/SVG2/shapes.html#PolygonElement>`__
        or a 
        `svg:polyline <https://www.w3.org/TR/SVG2/shapes.html#PolylineElement>`__
        element) that is drawn with the <SELF>.
        
        - The <SELF.Color> of the <SELF> is mapped to the :code:`stroke` attribute.
          For the attribute value, see the SVG mapping for :sp:element:`~Core.Diagram.Color`.
        
        - The <SELF.DashStyle> of the <SELF> is mapped to the :code:`stroke-dasharray` 
          and :code:`stroke-dashoffset` attributes as described in the SVG mapping for :sp:element:`~Core.Diagram.DashStyle`.
          Note that these attribute values depend on the <SELF.Width> of the <SELF> and
          on the :ref:`linecap` of the :sp:element:`~Core.Diagram.GraphicalPrimitive` that uses the <SELF>.
        
        - The <SELF.Width> of the <SELF> is mapped to the :code:`stroke-width` attribute.
          The attribute value is the concatenation of the string representation of the <SELF.Width> and
          the fixed string :code:`mm`. That is, in terms of :ref:`standard-css-values-4` we use an 
          `absolute length <https://www.w3.org/TR/css-values-4/#absolute-lengths>`__ with the unit millimeters.
        
        .. admonition:: example
        
            For examples, see the SVG mapping sections of those subclasses of :sp:element:`~Core.Diagram.GraphicalPrimitive`
            that have a <SELF> attribute:
        
            - :sp:element:`~Core.Diagram.Ellipse`
            - :sp:element:`~Core.Diagram.EllipseArc` 
            - :sp:element:`~Core.Diagram.Polygon` 
            - :sp:element:`~Core.Diagram.PolyLine`

    ''')

DIAGRAM.Stroke.Color = DATA_PROPERTY(
    description=r'''
        The color of the <OWNER>.
    ''',
    type=DIAGRAM.Color,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Color(
        R=0, G=0, B=255))

DIAGRAM.Stroke.DashStyle = DATA_PROPERTY(
    description=r'''
        The dash style of the <OWNER>.
    ''',
    type=DIAGRAM.DashStyle,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.DashStyle.Solid)

DIAGRAM.Stroke.Width = DATA_PROPERTY(
    description=r'''
        The width of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=2.)



################
#   Enumerations
################

DIAGRAM.AttributeRepresentationType = ENUMERATION()
DIAGRAM.AttributeRepresentationType.Value = ENUMERATION_LITERAL()
#TODO: no s
DIAGRAM.AttributeRepresentationType.Units = ENUMERATION_LITERAL()
#TODO: no s
DIAGRAM.AttributeRepresentationType.ValueAndUnits = ENUMERATION_LITERAL()

DIAGRAM.DashStyle = ENUMERATION(
    description=r'''
        A <!SELF> describes a pattern for drawing a stroke. The
        pattern gives the lengths of those parts of a stroke that are actually
        drawn and of those parts that are not drawn.
    ''',
    details=r'''
        Appearance
        ==========
        
        Each <!SELF> is characterized by a sequence of an even
        number of double values. The first of these values gives the
        length of a visible part of a stroke, the second one the length
        of an invisible part. Optional further pairs of double values in the
        pattern are applied in the same way. The entire pattern is applied
        repeatedly until the end of a stroke.
        
        The lengths in a <!SELF>'s pattern are given in terms
        of the :sp:element:`~Core.Diagram.Stroke`'s :sp:element:`~Core.Diagram.Stroke.Width` in mm, i.e., the dimensionless
        double values must be multiplied with the :sp:element:`~Core.Diagram.Stroke.Width` in
        order to get the actual lengths.
        
        The following table gives heuristically proven patterns for the different :sp:element:`DashStyles <Core.Diagram.DashStyle>`.
        
        .. image:: DashStyles.*
    ''')
DIAGRAM.DashStyle.Solid = ENUMERATION_LITERAL()
DIAGRAM.DashStyle.Dot = ENUMERATION_LITERAL()
DIAGRAM.DashStyle.Dash = ENUMERATION_LITERAL()
DIAGRAM.DashStyle.LongDash = ENUMERATION_LITERAL()

# TODO? check spec:Long Dash + Short Dash, CenterLine
DIAGRAM.DashStyle.LongDashShortDash = ENUMERATION_LITERAL()

DIAGRAM.DashStyle.ShortDash = ENUMERATION_LITERAL()
DIAGRAM.DashStyle.LongDashShortDashShortDash = ENUMERATION_LITERAL()
DIAGRAM.DashStyle.DashShortDash = ENUMERATION_LITERAL()

DIAGRAM.FillStyle = ENUMERATION()
DIAGRAM.FillStyle.Solid = ENUMERATION_LITERAL()
DIAGRAM.FillStyle.Transparent = ENUMERATION_LITERAL()
DIAGRAM.FillStyle.Hatch = ENUMERATION_LITERAL()

DIAGRAM.TextAlignment = ENUMERATION()
DIAGRAM.TextAlignment.LeftTop = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.LeftCenter = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.LeftBottom = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.CenterTop = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.CenterCenter = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.CenterBottom = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.RightTop = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.RightCenter = ENUMERATION_LITERAL()
DIAGRAM.TextAlignment.RightBottom = ENUMERATION_LITERAL()



###########
#   Classes
###########

DIAGRAM.GraphicalElement = ABSTRACT_CLASS()

DIAGRAM.GraphicalPrimitive = ABSTRACT_CLASS(
    superTypes=[DIAGRAM.GraphicalElement])

DIAGRAM.NodePosition = ABSTRACT_CLASS()

DIAGRAM.NodePosition.Position = DATA_PROPERTY(
    type=DIAGRAM.Point,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Point(
        X=3.5, Y=5.5))

DIAGRAM.Ellipse = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalPrimitive],
    description='''
        An ellipse.''',
    details=r'''
        Geometry
        ========
        
        The geometry of an <!SELF> is characterized by its
        <SELF.Center>, its two axes (<SELF.HorizontalSemiAxis>
        and <SELF.VerticalSemiAxis>), and the <SELF.Rotation>
        of the <SELF.HorizontalSemiAxis> w.r.t. the x axis of the
        :ref:`owner <owner-of-graphical-primitive>`. The <SELF.Rotation>
        is measured clockwise and in degrees.
        
        .. admonition:: example
        
            We consider an <!SELF> with 
            
            - <SELF.Center> :code:`(10, 20)`,
            
            - <SELF.HorizontalSemiAxis> :code:`110`,
            
            - <SELF.VerticalSemiAxis> :code:`50`, and
            
            - <SELF.Rotation> :code:`35`.
            
            The <!SELF> will look like this:
            
            .. image:: EllipseGeometry.*
           
        .. rubric:: Visual Center
        
        The :ref:`visual center <visual-center>` of an <!SELF>
        is its actual <SELF.Center>.
        
        Mapping to SVG
        ==============
        
        An <SELF> corresponds to an
        `svg:ellipse
        <https://www.w3.org/TR/SVG2/shapes.html#EllipseElement>`__
        with these attributes:
        
        - :code:`transform` describes both the <SELF.Center> :math:`(c_x, c_y)` and the
          <SELF.Rotation> :math:`r` of the Ellipse.
        
          :code:`transform = "translate(` + str(:math:`c_x`) + :code:`,` + str(:math:`c_y`) + :code:`) rotate(` + str(:math:`r`) + :code:`)"`
        
        - :code:`rx` and :code:`ry` are string representations of <SELF.HorizontalSemiAxis> and <SELF.VerticalSemiAxis>.
        
        - :code:`stroke`, :code:`stroke-dasharray`, :code:`stroke-dashoffset`
          and :code:`stroke-width`
          are set according to the SVG mapping rules for the 
          <SELF.Stroke> of the <SELF> (see
          :sp:element:`~Core.Diagram.Stroke`).
        
        - :code:`stroke-linecap = "round"` and 
          :code:`stroke-linejoin = "round"` reflect the
          :ref:`heuristic for line caps and line joins
          <line-caps-and-line-joins>`.
        
        - :code:`vector-effect = "non-scaling-stroke"` reflects the
          :ref:`heuristic for scaled symbols <scaled-symbols>`.
        
        - :code:`fill` is set according to the SVG mapping rules for
          the <SELF.FillStyle> of the <SELF> (see
          :sp:element:`~Core.Diagram.FillStyle`).
          
        .. admonition:: example
        
            We assume that the :sp:element:`~Core.Diagram.Stroke` of the <SELF> above is
            :code:`2mm #ff0000 Solid` and that its <SELF.FillStyle> is
            :sp:element:`~Core.Diagram.FillStyle.Transparent`.
            
            .. code-block:: xml
            
               {EllipseTransparentSvgCode}
            
            .. image:: EllipseTransparentSvg.*
            
        .. admonition:: example
        
            We consider the same <SELF> as in the previous example,
            except that the :sp:element:`~Core.Diagram.Stroke` is
            :code:`2mm #ff0000 LongDashShortDash`.
            
            .. code-block:: xml
            
               {EllipseLongDashShortDashSvgCode}
            
            .. image:: EllipseLongDashShortDashSvg.*
        
        .. admonition:: example
        
            Finally, a variant with :sp:element:`~Core.Diagram.Stroke` :code:`2mm #ff0000 Solid`
            and <SELF.FillStyle> :sp:element:`~Core.Diagram.FillStyle.Hatch`.
            
            .. code-block:: xml
            
               {EllipseHatchSvgCode}
            
            .. image:: EllipseHatchSvg.*
    ''')

DIAGRAM.Ellipse.Center = DATA_PROPERTY(
    description=r'''
        The center position of the <OWNER>.
    ''',
    type=DIAGRAM.Point,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Point(
        X=0.0, Y=0.0))

DIAGRAM.Ellipse.FillStyle = DATA_PROPERTY(
    description=r'''
        The fill style of the <OWNER>.
    ''',
    type=DIAGRAM.FillStyle,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.FillStyle.Transparent)

DIAGRAM.Ellipse.HorizontalSemiAxis = DATA_PROPERTY(
    description=r'''
        The length of the horizontal semi-axis of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=7.5)

DIAGRAM.Ellipse.Rotation = DATA_PROPERTY(
    description=r'''
        The rotation of the <OWNER> around its center, measured clockwise and in degrees.
        The value must be in the inverval [0; 360).
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=270.)

DIAGRAM.Ellipse.Stroke = DATA_PROPERTY(
    description=r'''
        The stroke of the <OWNER>.
    ''',
    type=DIAGRAM.Stroke,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Stroke(
        Color=DIAGRAM.Color(R=128, G=0, B=0),
        DashStyle=DIAGRAM.DashStyle.Solid,
        Width=0.3))

DIAGRAM.Ellipse.VerticalSemiAxis = DATA_PROPERTY(
    description=r'''
        The length of the vertical semi-axis of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=7.5)

DIAGRAM.EllipseArc = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalPrimitive],
    description=r''''
        A segment of an ellipse.
    ''',
    details=r'''
        Geometry
        ========
        
        An <!SELF> is a segment of an ellipse. The geometry
        of the underlying ellipse is described in the same way as the
        geometry of the actual :sp:element:`~Core.Diagram.Ellipse` class (<SELF.Center>, 
        <SELF.HorizontalSemiAxis>,
        <SELF.VerticalSemiAxis>,
        <SELF.Rotation>). In addition, an <!SELF>
        has two attributes <SELF.StartAngle> and 
        <SELF.EndAngle> that determine the start and end position
        of the arc.
        
        .. admonition:: example
        
            We consider an <SELF> with
            
            - <SELF.Center> :code:`(10, 20)`,
            
            - <SELF.HorizontalSemiAxis> :code:`110`,
            
            - <SELF.VerticalSemiAxis> :code:`50`, and
            
            - <SELF.Rotation> :code:`35`.
            
            These attributes describe the blue dashed ellipse in this figure
            (cf. the :sp:element:`~Core.Diagram.Ellipse` example which has the same attribute values).
            
            .. image:: EllipseArcGeometry.*
            
            The <SELF> has two further geometric attributes
            
            - <SELF.StartAngle> :code:`288` and
            
            - <SELF.EndAngle> :code:`20`.
            
            These two angles do not have a simple geometric interpretation in the
            figure; we will get back to them in the following sections.
            However, these angles determine the start position and the end position
            of the black <SELF> in the figure. The actual
            <SELF> goes from the start position *in
            positive direction* (i.e., clockwise) to the end position.

        .. rubric:: Calculation of start and end position
        
        We use the following notation:
        
        - :math:`c_x` and :math:`c_y`: components of the <SELF.Center>,
        
        - :math:`r_x`: <SELF.HorizontalSemiAxis>,
        
        - :math:`r_y`: <SELF.VerticalSemiAxis>,
        
        - :math:`\varphi`: <SELF.Rotation>,
        
        - :math:`\theta_1`: <SELF.StartAngle>,
        
        - :math:`\theta_2`: <SELF.EndAngle>,
        
        - :math:`x_1` and :math:`y_1`: start position,
        
        - :math:`x_2` and :math:`y_2`: end position.
        
        .. admonition:: technical
        
            The notation is based on that used by the
            `SVG Arc Implementation Notes <https://www.w3.org/TR/SVG2/implnote.html#ArcImplementationNotes>`__
            which may be useful for implementors. 
        
        The start position is
        
        .. math::
        
           \left(\begin{array}{c} x_1 \\ y_1 \end{array}\right) = 
             \left(\begin{array}{cc} \cos \varphi & -\sin \varphi \\ \sin \varphi & \cos \varphi \end{array}\right)
             \cdotp
             \left(\begin{array}{c} r_x \cos \theta_1 \\ r_y \sin \theta_1 \end{array}\right)
             +
             \left(\begin{array}{c} c_x \\ c_y \end{array}\right)
        
        and the end position is
        
        .. math::
        
           \left(\begin{array}{c} x_2 \\ y_2 \end{array}\right) = 
             \left(\begin{array}{cc} \cos \varphi & -\sin \varphi \\ \sin \varphi & \cos \varphi \end{array}\right)
             \cdotp
             \left(\begin{array}{c} r_x \cos \theta_2 \\ r_y \sin \theta_2 \end{array}\right)
             +
             \left(\begin{array}{c} c_x \\ c_y \end{array}\right) \quad .
        
        .. admonition:: example
        
            In the example, we have
            
            .. math::
            
               c_x &= 10 
            
               c_y &= 20 
            
               r_x &= 110 
            
               r_y &= 50 
            
               \varphi &= 35 
            
               \theta_1 &= 288 
            
               \theta_2 &= 20 
            
            With the equations above, we get these coordinates for the
            start and end positions (cf. the figure above):
            
            .. math::
            
               x_1 &= 65.1197
            
               y_1 &= 0.5439
            
               x_2 &= 84.8639
            
               y_2 &= 93.2967
        
        .. rubric:: Interpretation of StartAngle and EndAngle
        
        These angles are not measured in the ellipse on which an
        <SELF> is based, but in the unit circle:
        
        .. image:: EllipseArcExplanation.*
        
        The figure shows the end position w.r.t. the unit circle. Its angle
        measured from the horizonal semi-axis is :math:`\theta_2 = 20`.
        The ellipse could be constructed by stretching the unit circle 
        by :math:`r_x` in direction of the horizontal semi-axis and by 
        :math:`r_y` in direction of the vertical semi-axis. After this
        transformation, the end position w.r.t. the unit circle is at the
        actual end position.
        
        To calculate an actual, ellipse-based angle from an angle w.r.t. the unit circle,
        use the formula
        
        .. math::
        
           \theta_{actual} = \textrm{atan2}( r_y  \sin \theta, r_x  \cos \theta ) \,\textrm{mod}\, 360 \quad.
        
        The formulas apply to both the  <SELF.StartAngle> :math:`\theta_1` 
        and the <SELF.EndAngle> :math:`\theta_2`. Note that we give
        angles in degrees, i.e., the actual calculations in a program may require conversions
        to and from radians. 
        
        .. admonition:: example
        
            In the example, we have
            
            .. math::
            
                \theta_{actual, 1} = \textrm{atan2}( 50 \cdotp \sin 288, 110 \cdotp \cos 288) \,\textrm{mod}\, 360 = 305.56 
            
            and 
            
            .. math::
            
                \theta_{actual, 2} = \textrm{atan2}( 50 \cdotp \sin 20, 110 \cdotp \cos 20)   \,\textrm{mod}\, 360 = 9.39 \quad .
        
        The inverse formula is
        
        .. math::
        
            \theta = \textrm{atan2}( r_x  \sin \theta_{actual}, r_y  \cos \theta_{actual} ) \,\textrm{mod}\, 360 \quad .
        
        .. admonition:: technical
        
            The rationale for using angles w.r.t. the unit circle is that they
            are numerically more stable when an <SELF> is scaled
            with small values (i.e., in a :sp:element:`~Core.Diagram.ShapeUsage`) and that some
            calculations are simpler (cf.
            `SVG 2 Arc Implementation Notes <https://www.w3.org/TR/SVG2/implnote.html#ArcImplementationNotes>`__).
            
        Mapping to SVG
        ==============
        
        An <SELF> is mapped to an 
        `svg:path
        <https://www.w3.org/TR/SVG2/paths.html#PathElement>`__
        with these attributes:
        
        - :code:`d` is the `path data <https://www.w3.org/TR/SVG2/paths.html#PathData>`__
          that describes the entire geometry of the <SELF>. The
          value is the concatenation of the following strings, all of them separated by spaces:
        
          - :code:`M`
        
          - str(:math:`x_1`)
        
          - str(:math:`y_1`)
        
          - :code:`A`
        
          - str(:math:`r_x`)
        
          - str(:math:`r_y`)
        
          - str(:math:`\varphi`)
        
          - str(:math:`f_A`)
        
          - :code:`1`
        
          - str(:math:`x_2`)
        
          - str(:math:`y_2`)
        
          :math:`f_A` is calculated as follows (cf. the definition of the
          :ref:`modulo operator <modulo-operator>`):
        
          .. math::
        
             \Delta \theta &= (\theta_2 - \theta_1)\, \textrm{mod}\, 360 \quad ,
        
             f_A &= 0 \quad \textrm{if} \, \Delta \theta < 180 \quad ,
             
             f_A &= 1 \quad \textrm{if} \, \Delta \theta \geq 180 \quad .
        
          The other variables have been defined above.
        
        - :code:`stroke`, :code:`stroke-dasharray`, :code:`stroke-dashoffset`
          and :code:`stroke-width`
          are set according to the SVG mapping rules for the 
          <SELF.Stroke> of the <SELF> (see
          :sp:element:`~Core.Diagram.Stroke`).
        
        - :code:`stroke-linecap = "round"` and 
          :code:`stroke-linejoin = "round"` reflect the
          :ref:`heuristic for line caps and line joins
          <line-caps-and-line-joins>`.
        
        - :code:`vector-effect = "non-scaling-stroke"` reflects the
          :ref:`heuristic for scaled symbols <scaled-symbols>`.
        
        - :code:`fill = "none"` is required to avoid that the `svg:path
          <https://www.w3.org/TR/SVG2/shapes.html#PolylineElement>`__ is
          filled.

        .. admonition:: example
       
            We assume that the :sp:element:`~Core.Diagram.Stroke` of the <SELF> above is
            :code:`2mm #ff0000 solid`.
            
            With :math:`\Delta \theta = (20 - 288)\, \textrm{{mod}}\,360 = (-268)\, \textrm{{mod}}\, 360 = 92 < 180`
            we get :math:`f_A = 0`.
            
            .. code-block:: xml
            
               {EllipseArcSolidSvgCode}
            
            .. image:: EllipseArcSolidSvg.*       
       
        .. admonition:: example
       
           We consider the same <SELF> as in the previous example,
           except that the :sp:element:`~Core.Diagram.Stroke` is
           :code:`2mm #ff0000 Dash`.
       
           .. code-block:: xml
       
              {EllipseArcDashSvgCode}
       
           .. image:: EllipseArcDashSvg.*
        
    ''')

DIAGRAM.EllipseArc.Center = DATA_PROPERTY(
    description=r'''
        The center position of the <OWNER>.
    ''',
    type=DIAGRAM.Point,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Point(
        X=2.0, Y=5.0))

DIAGRAM.EllipseArc.EndAngle = DATA_PROPERTY(
    description=r'''
        The end angle of the <OWNER>, measured clockwise and in degrees.
        The value must be in the inverval [0; 360).
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=270.)

DIAGRAM.EllipseArc.HorizontalSemiAxis = DATA_PROPERTY(
    description=r'''
        The length of the horizontal semi-axis of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=7.5)

DIAGRAM.EllipseArc.StartAngle = DATA_PROPERTY(
    description=r'''
        The start angle of the <OWNER>, measured clockwise and in degrees.
        The value must be in the inverval [0; 360).
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=90.)

DIAGRAM.EllipseArc.Rotation = DATA_PROPERTY(
    description=r'''
        The rotation of the <OWNER> around its center, measured clockwise and in degrees.
        The value must be in the inverval [0; 360).
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=270.)

DIAGRAM.EllipseArc.Stroke = DATA_PROPERTY(
    description=r'''
        The stroke of the <OWNER>.
    ''',
    type=DIAGRAM.Stroke,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Stroke(
        Color=DIAGRAM.Color(R=128, G=0, B=0),
        DashStyle=DIAGRAM.DashStyle.Solid,
        Width=0.3))

DIAGRAM.EllipseArc.VerticalSemiAxis = DATA_PROPERTY(
    description=r'''
        The length of the vertical semi-axis of the <OWNER> in mm.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=3.5)

DIAGRAM.Polygon = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalPrimitive],
    description=r'''
        A figure that is delimited by a closed chain of three or more straight sections.
    ''',
    details=r'''
        Geometry
        ========

        The first straight section that delimits a <!SELF> starts at
        its first :sp:element:`~Core.Diagram.Point`, i.e., :sp:element:`Points[0] <Core.Diagram.Polygon.Points>`, and ends at its
        second :sp:element:`~Core.Diagram.Point`. For each
        further :sp:element:`~Core.Diagram.Point`, another section is
        added that starts at the preceding :sp:element:`~Core.Diagram.Point`. Finally, a section
        is added that starts at the last :sp:element:`~Core.Diagram.Point` and goes back to the first
        :sp:element:`~Core.Diagram.Point` such that the chain of sections is closed.
        
        .. admonition:: example
        
            We consider a <SELF> with 4 <SELF.Points>:
            
            - :code:`(-30, 40)`,
            
            - :code:`(50, 40)`,
            
            - :code:`(-10, -60)`, and            
            
            - :code:`(-10, 0)`.
            
            The <SELF> will look like this:
            
            .. image:: PolygonGeometry.*
        
        .. rubric:: Interior of a Polygon
        
        Depending on its <SELF.FillStyle>, the interior of a
        <SELF> may be filled. There are several possibilities to 
        define when *"a point is inside a polygon"*. DEXPI applies a simple
        intuitive rule:
        
        - Choose an arbitrary point outside the
          :ref:`geometric bounding box <geometric bounding box>` of the <SELF>.
        
        - Each point that can be reached from there without crossing any
          segment is outside the <SELF>.
        
        - Each other point is inside the <SELF>.
        
        .. admonition:: example
        
            The grey area in the figure visualizes the interior of the given
            <SELF>.
            
            .. image:: PolygonNonzeroRule.*
        
        .. admonition:: technical
        
            In case of polygons, the DEXPI definition for interior points 
            coincides with the *nonzero rule* in SVG. See
            `Section 13.4.2. of the SVG 2 Recommendation <https://www.w3.org/TR/SVG2/painting.html#WindingRule>`__
            for a more precise definition of the *nonzero rule*.
            
            The SVG 2 Recommendation also defines an alternative rule called
            *evenodd rule*. If we applied this rule, the pentagonal area in the
            center of this <SELF> would be considered outside:
            
            .. image:: PolygonEvenoddRule.*
        
        .. rubric:: Visual Center
        
        Let :math:`n` be the number of <SELF.Points>, and let :math:`x_i`
        and :math:`y_i` be the :sp:element:`~Core.Diagram.Point.X` and :sp:element:`~Core.Diagram.Point.Y` positions
        of :sp:element:`Point <Core.Diagram.Polygon.Points>` :math:`i` for :math:`0 \leq i < n`.
        
        Then the horizontal position :math:`c_x` and the vertical position 
        :math:`c_y` of the :ref:`visual center <visual-center>` of the <SELF> are
        
        .. math::
        
           c_x &= \frac 1 2 \Big[ \min_{i=0}^{n-1} x_i + \max_{i=0}^{n-1} x_i \Big] \quad ,
        
           c_y &= \frac 1 2 \Big[ \min_{i=0}^{n-1} y_i + \max_{i=0}^{n-1} y_i \Big] \quad .
        
        Intuitively, the :ref:`visual center <visual-center>` is
        the center of the minimum bounding box that contains all
        <SELF.Points>.
        
        If the <SELF> has the <SELF.FillStyle> :sp:element:`~Core.Diagram.FillStyle.Hatch`,
        then one of the hatch lines will cross through the visual center.
        
        .. admonition:: example
        
            For the <SELF> above, we have
            
            .. math::
            
               c_x &= \frac 1 2 [ \min(-30, 50, -10, -10) + \max(-30, 50, -10, -10) ]
            
                   &= \frac 1 2 [-30 + 50]
            
                   &= 10
            
            and 
            
            .. math::
            
               c_y &= \frac 1 2 [ \min(40, 40, -60, 0) + \max(40, 40, -60, 0) ]
            
                   &= \frac 1 2 [-60 + 40]
            
                   &= -10 \quad .

        Mapping to SVG
        ==============

        A <SELF> corresponds to an
        `svg:polygon <https://www.w3.org/TR/SVG2/shapes.html#PolygonElement>`__
        with these attributes:
        
        - :code:`transform` contains a translation from the origin to the
          visual center. This is required due to the modified positions in
          :code:`points`.
        
          :code:`transform = "translate(` + str(:math:`c_x`) + :code:`,` + str(:math:`c_y`) + :code:`)"`
        
        - :code:`points` contains the <SELF.Points> of the
          <SELF> *relative to the visual center*.
        
          For each :sp:element:`~Core.Diagram.Point` :math:`i` with (absolute) position 
          :math:`x_i` and :math:`y_i`, 
          the position relative to the visual center is
        
          .. math::
        
             \tilde{x}_i &= x_i - c_x \quad ,
        
             \tilde{y}_i &= y_i - c_y \quad .
        
          Each of the relative positions is converted to a string as
          str(:math:`\tilde{x}_i`) + :code:`,` + str(:math:`\tilde{y}_i`).
          Finally, the :code:`points` attribute is set to a single string that contains
          all relative positions, separated by spaces.
        
        - :code:`stroke`, :code:`stroke-dasharray`, :code:`stroke-dashoffset`
          and :code:`stroke-width`
          are set according to the SVG mapping rules for the 
          <SELF.Stroke> of the <SELF> (see
          :sp:element:`~Core.Diagram.Stroke`).
        
        - :code:`stroke-linecap = "round"` and 
          :code:`stroke-linejoin = "round"` reflect the
          :ref:`heuristic for line caps and line joins
          <line-caps-and-line-joins>`.
        
        - :code:`vector-effect = "non-scaling-stroke"` reflects the
          :ref:`heuristic for scaled symbols <scaled-symbols>`.
        
        - :code:`fill` is set according to the SVG mapping rules for
          the <SELF.FillStyle> of the <SELF> (see
          :sp:element:`~Core.Diagram.FillStyle`).
        
        .. admonition:: example
        
            We assume that the :sp:element:`~Core.Diagram.Stroke` of the <SELF> above is
            :code:`2mm #ff00ff Solid` and that its <SELF.FillStyle> is
            :sp:element:`~Core.Diagram.FillStyle.Transparent`.
            
            .. code-block:: xml
            
               {PolygonTransparentSvgCode}
            
            .. image:: PolygonTransparentSvg.*
        
        .. admonition:: example
        
            We consider the same <SELF> as in the previous example,
            except that the :sp:element:`~Core.Diagram.Stroke` is
            :code:`2mm #ff00ff Dot`.
            
            .. code-block:: xml
            
               {PolygonDotSvgCode}
            
            .. image:: PolygonDotSvg.*
        
        .. admonition:: example
        
            Finally, a variant with :sp:element:`~Core.Diagram.Stroke` :code:`2mm #ff00ff Solid`
            and <SELF.FillStyle> :sp:element:`~Core.Diagram.FillStyle.Hatch`.
            
            .. code-block:: xml
            
               {PolygonHatchSvgCode}
            
            .. image:: PolygonHatchSvg.*

    ''')

DIAGRAM.Polygon.FillStyle = DATA_PROPERTY(
    description=r'''
        The fill style of the <OWNER>.
    ''',
    type=DIAGRAM.FillStyle,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.FillStyle.Transparent)

DIAGRAM.Polygon.Points = DATA_PROPERTY(
    description=r'''
        The points (vertices) of the <OWNER>.
    ''',
    type=DIAGRAM.Point,
    lower=3,
    upper=None,
    isOrdered=True,
    isUnique=False,
    exampleValue=[
        DIAGRAM.Point(X=3.5, Y=5.5),
        DIAGRAM.Point(X=5.5, Y=7.5),
        DIAGRAM.Point(X=1.5, Y=9.5)])

DIAGRAM.Polygon.Stroke = DATA_PROPERTY(
    description=r'''
        The stroke of the <OWNER>.
    ''',
    type=DIAGRAM.Stroke,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Stroke(
        Color=DIAGRAM.Color(R=128, G=0, B=0),
        DashStyle=DIAGRAM.DashStyle.Solid,
        Width=0.3))

DIAGRAM.PolyLine = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalPrimitive],
    description=r'''
        A curve that consists of one or more chained straight sections.
    ''',
    details=r'''
        Geometry
        ========

        The first straight section of a <SELF> starts at its first
        :sp:element:`~Core.Diagram.Point`, i.e., :sp:element:`Points[0] <Core.Diagram.Polygon.Points>`, and ends at its
        second :sp:element:`~Core.Diagram.Point`. For each
        further :sp:element:`~Core.Diagram.Point`, another section is
        drawn that starts at the preceding :sp:element:`~Core.Diagram.Point`.
        
        .. admonition:: example
        
            We consider a <SELF> with 3 <SELF.Points>:
            
            - :code:`(-30, 40)`,
            
            - :code:`(50, 40)`, and
            
            - :code:`(-10, -60)`.
            
            The <SELF> will look like this:
            
            .. image:: PolyLineGeometry.*

        Mapping to SVG
        ==============

        A <SELF> corresponds to an
        `svg:polyline
        <https://www.w3.org/TR/SVG2/shapes.html#PolylineElement>`__
        with these attributes:
        
        - :code:`points` contains the <SELF.Points> of the
          <SELF>.
        
          Each :sp:element:`~Core.Diagram.Point` :math:`i` with position 
          :math:`x_i` and :math:`y_i` is converted to a string as
          str(:math:`x_i`) + :code:`,` + str(:math:`y_i`).
          Finally, the :code:`points` attribute is set to a single string that contains
          all positions, separated by spaces.
        
        - :code:`stroke`, :code:`stroke-dasharray`, :code:`stroke-dashoffset`
          and :code:`stroke-width`
          are set according to the SVG mapping rules for the 
          <SELF.Stroke> of the <SELF> (see
          :sp:element:`~Core.Diagram.Stroke`).
        
        - :code:`stroke-linecap = "round"` and 
          :code:`stroke-linejoin = "round"` reflect the
          :ref:`heuristic for line caps and line joins
          <line-caps-and-line-joins>`.
        
        - :code:`vector-effect = "non-scaling-stroke"` reflects the
          :ref:`heuristic for scaled symbols <scaled-symbols>`.
        
        - :code:`fill = "none"` is required to avoid that the `svg:polyline
          <https://www.w3.org/TR/SVG2/shapes.html#PolylineElement>`__ is
          filled.
        
        .. admonition:: example
        
            We assume that the :sp:element:`~Core.Diagram.Stroke` of the <SELF> above is
            :code:`2mm #007fff solid`.
            
            .. code-block:: xml
            
               {PolyLineSolidSvgCode}
            
            .. image:: PolyLineSolidSvg.*
        
        .. admonition:: example
        
            We consider the same <SELF> as in the previous example,
            except that the :sp:element:`~Core.Diagram.Stroke` is
            :code:`2mm #007fff Dash`.
            
            .. code-block:: xml
            
               {PolyLineDashSvgCode}
            
            .. image:: PolyLineDashSvg.*
    
    ''')

DIAGRAM.PolyLine.Points = DATA_PROPERTY(
    description=r'''
        The points of the <OWNER>.
    ''',
    type=DIAGRAM.Point,
    lower=2,
    upper=None,
    isOrdered=True,
    isUnique=False,
    exampleValue=[
        DIAGRAM.Point(X=3.5, Y=5.5),
        DIAGRAM.Point(X=5.5, Y=7.5)])

DIAGRAM.PolyLine.Stroke = DATA_PROPERTY(
    description=r'''
        The stroke of the <OWNER>.
    ''',
    type=DIAGRAM.Stroke,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Stroke(
        Color=DIAGRAM.Color(R=128, G=0, B=0),
        DashStyle=DIAGRAM.DashStyle.Solid,
        Width=0.3))

DIAGRAM.Text = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalPrimitive])

DIAGRAM.Text.Alignment = DATA_PROPERTY(
    type=DIAGRAM.TextAlignment,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.TextAlignment.CenterBottom)

DIAGRAM.Text.Color = DATA_PROPERTY(
    type=DIAGRAM.Color,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Color(
        R=0, G=0, B=0))

DIAGRAM.Text.Font = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Calibri')

DIAGRAM.Text.Position = DATA_PROPERTY(
    type=DIAGRAM.Point,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Point(
        X=9.7, Y=16.64))

DIAGRAM.Text.Rotation = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=0.0)

DIAGRAM.Text.Size = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=3.0)

DIAGRAM.Text.Text = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='N1')

DIAGRAM.Text.Template = COMPOSITION_PROPERTY(
    description=r'''
        The template that describes how the text is built.
    ''',
    type=DIAGRAM.TextTemplate,
    lower=0,
    upper=1)

DIAGRAM.TextTemplateFragment = ABSTRACT_CLASS()

DIAGRAM.TextTemplate = CONCRETE_CLASS()

DIAGRAM.TextTemplate.Fragments = COMPOSITION_PROPERTY(
    description=r'''
        The fragments of the <OWNER>.
    ''',
    type=DIAGRAM.TextTemplateFragment,
    lower=0,
    upper=None,
    isOrdered=True)

DIAGRAM.AttributeRepresentation = CONCRETE_CLASS(
    superTypes=[DIAGRAM.TextTemplateFragment])

DIAGRAM.AttributeRepresentation.AttributeName = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='SubTagName')

DIAGRAM.AttributeRepresentation.Type = DATA_PROPERTY(
    type=DIAGRAM.AttributeRepresentationType,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.AttributeRepresentationType.Value)

DIAGRAM.AttributeRepresentation.Object = REFERENCE_PROPERTY(
    type=Core.ConceptualObject,
    lower=1,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

DIAGRAM.ConnectorLine = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalPrimitive])

DIAGRAM.ConnectorLine.InnerPoints = DATA_PROPERTY(
    description=r'''
        The inner points of the <OWNER>.
    ''',
    type=DIAGRAM.Point,
    lower=0,
    upper=None,
    isOrdered=True,
    isUnique=False,
    exampleValue=[DIAGRAM.Point(
        X=9.7, Y=16.64)])

DIAGRAM.ConnectorLine.Stroke = DATA_PROPERTY(
    description=r'''
        The stroke of the <OWNER>.
    ''',
    type=DIAGRAM.Stroke,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Stroke(
        Color=DIAGRAM.Color(R=128, G=0, B=0),
        DashStyle=DIAGRAM.DashStyle.Solid,
        Width=0.3))

DIAGRAM.ConnectorLine.Source = REFERENCE_PROPERTY(
    type=DIAGRAM.NodePosition,
    lower=0, # TODO: 1
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

DIAGRAM.ConnectorLine.Target = REFERENCE_PROPERTY(
    type=DIAGRAM.NodePosition,
    lower=0, # TODO: 1
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

DIAGRAM.GraphicsGroup = ABSTRACT_CLASS()

DIAGRAM.RepresentationGroup = CONCRETE_CLASS(
    description='''
        A <!SELF> is a graphical representation of a :sp:element:`~Core.ConceptualObject`.''',
    superTypes=[DIAGRAM.GraphicsGroup])

DIAGRAM.RepresentationGroup.NodePositions = COMPOSITION_PROPERTY(
    description=r'''
        The node positions of the <OWNER>.
    ''',
    type=DIAGRAM.NodePosition, # TODO: only instru?
    lower=0,
    upper=None)

DIAGRAM.RepresentationGroup.Groups = COMPOSITION_PROPERTY(
    description=r'''
        The groups of the <OWNER>.
    ''',
    type=DIAGRAM.GraphicsGroup,
    lower=0,
    upper=None,
    isOrdered=True)

DIAGRAM.RepresentationGroup.Represents = REFERENCE_PROPERTY(
    description=r'''
        The object represented by the <OWNER>.
    ''',
    type=Core.ConceptualObject,
    lower=1,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

DIAGRAM.Diagram = CONCRETE_CLASS(
    superTypes=[DIAGRAM.RepresentationGroup])

DIAGRAM.Diagram.BackgroundColor = DATA_PROPERTY(
    type=DIAGRAM.Color,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Color(
        R=255, G=255, B=255))

DIAGRAM.Diagram.MaxX = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=100.0)

DIAGRAM.Diagram.MaxY = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=40.0)

DIAGRAM.Diagram.MinX = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=0.0)

DIAGRAM.Diagram.MinY = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=0.0)

DIAGRAM.Diagram.Name = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Example P&ID')

DIAGRAM.RepresentationTypeGroup = ABSTRACT_CLASS(
    superTypes=[DIAGRAM.GraphicsGroup])

DIAGRAM.RepresentationTypeGroup.Elements = COMPOSITION_PROPERTY(
    description=r'''
        The graphical elements of the <OWNER>.
    ''',
    type=DIAGRAM.GraphicalElement,
    lower=0,
    upper=None,
    isOrdered=True)

DIAGRAM.Border = CONCRETE_CLASS(
    superTypes=[DIAGRAM.RepresentationTypeGroup])

DIAGRAM.Static = CONCRETE_CLASS(
    superTypes=[DIAGRAM.RepresentationTypeGroup])

DIAGRAM.Label = CONCRETE_CLASS(
    superTypes=[DIAGRAM.RepresentationTypeGroup])

DIAGRAM.LiteralText = CONCRETE_CLASS(
    superTypes=[DIAGRAM.TextTemplateFragment])

DIAGRAM.LiteralText.Text = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Drawing No.: ')

DIAGRAM.MetaData = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.META_DATA,
    description=r'''
        Meta data about a :sp:element:`~Core.Container`.
    ''')

DIAGRAM.MetaData.ApprovalDateRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.APPROVAL_DATE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A representation of the approval date of the drawing. The format of the
        representation is not prescribed.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='2016-04-01')

DIAGRAM.MetaData.ApprovalDescription = DATA_PROPERTY(
    rdl=DEXPI_RDL.APPROVAL_DESCRIPTION_ASSIGNMENT_CLASS,
    description=r'''
        A description of the approval of the drawing.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=DATA_TYPES.MultiLanguageString(
        SingleLanguageStrings = [
            DATA_TYPES.SingleLanguageString(
                Language='en', Value='approved'),
            DATA_TYPES.SingleLanguageString(
                Language='de', Value='genehmigt')]))


DIAGRAM.MetaData.ApproverName = DATA_PROPERTY(
    rdl=DEXPI_RDL.APPROVER_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the approver of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='A. P. Prover')

DIAGRAM.MetaData.ArchiveNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.ARCHIVE_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The archive number of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='XY923-463')

DIAGRAM.MetaData.BlockName = DATA_PROPERTY(
    rdl=DEXPI_RDL.BLOCK_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the related block.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='a block')

DIAGRAM.MetaData.BlockNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.BLOCK_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the related block.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='B987-654')

DIAGRAM.MetaData.CheckerName = DATA_PROPERTY(
    rdl=DEXPI_RDL.CHECKER_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the checker of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='C. Hecker')

DIAGRAM.MetaData.Confidentiality = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONFIDENTIALITY_SPECIALIZATION,
    description=r'''
        The confidentiality classification of the diagram.
    ''',
    type=DIAGRAM.ConfidentialityClassification,
    lower=0,
    upper=1,
    exampleValue=DIAGRAM.ConfidentialityClassification.ConfidentialInformation)

DIAGRAM.MetaData.CreationDateRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.CREATION_DATE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A representation of the creation date of the drawing. The format of the
        representation is not prescribed.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='2016-04-01')

DIAGRAM.MetaData.CreatorName = DATA_PROPERTY(
    rdl=DEXPI_RDL.CREATOR_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the creator of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='A. Creator')

DIAGRAM.MetaData.DesignerName = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGNER_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the designer of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='D. E. Signer')

DIAGRAM.MetaData.DrafterName = DATA_PROPERTY(
    rdl=DEXPI_RDL.DRAFTER_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the drafter of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='D. Rafter')

DIAGRAM.MetaData.DrawingName = DATA_PROPERTY(
    rdl=JORD_RDL.DRAWING_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The drawing name.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DEXPI example PID')

DIAGRAM.MetaData.DrawingNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.DRAWING_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The drawing number.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='123/A93')

DIAGRAM.MetaData.DrawingSubTitle = DATA_PROPERTY(
    rdl=DEXPI_RDL.DRAWING_SUB_TITLE_ASSIGNMENT_CLASS,
    description=r'''
        The subtitle of the drawing.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=DATA_TYPES.MultiLanguageString(
        SingleLanguageStrings = [
            DATA_TYPES.SingleLanguageString(
                Language='en', Value='DEXPI Example PID'),
            DATA_TYPES.SingleLanguageString(
                Language='de', Value='DEXPI Beispiel-R&I')]))

DIAGRAM.MetaData.FileName = DATA_PROPERTY(
    rdl=DEXPI_RDL.FILE_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The file name of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DEXPI_example_PID.xml')

DIAGRAM.MetaData.LastModificationDateRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.LAST_MODIFICATION_DATE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A representation of the last modification date of the drawing. The format of the
        representation is not prescribed.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='2016-04-02')

DIAGRAM.MetaData.LocationName = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The location name.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='C1248')

DIAGRAM.MetaData.ProcessCellIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_CELL_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the related process cell according to ISA-95.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='PC123')

DIAGRAM.MetaData.ProcessCellName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_CELL_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the related process cell according to ISA-95.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='a process cell')

DIAGRAM.MetaData.ProjectName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROJECT_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the related project.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='a project')

DIAGRAM.MetaData.ProjectNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROJECT_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the related project.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='P3.1415')

DIAGRAM.MetaData.ProjectRangeNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROJECT_RANGE_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The range number of the related project.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='PR321')

DIAGRAM.MetaData.ReplacedDrawing = DATA_PROPERTY(
    rdl=DEXPI_RDL.REPLACED_DRAWING_ASSIGNMENT_CLASS,
    description=r'''
        The drawing replaced by this drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='D321')

DIAGRAM.MetaData.ResponsibleDepartmentName = DATA_PROPERTY(
    rdl=DEXPI_RDL.RESPONSIBLE_DEPARTMENT_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the department responsible for the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='R2-D2')

DIAGRAM.MetaData.RevisionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.REVISION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The revision number of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='R2.2')

DIAGRAM.MetaData.SheetFormat = DATA_PROPERTY(
    rdl=DEXPI_RDL.SHEET_FORMAT_ASSIGNMENT_CLASS,
    description=r'''
        The sheet format.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DIN A3')

DIAGRAM.MetaData.SheetNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.SHEET_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The sheet number of the drawing.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='2a')

DIAGRAM.MetaData.SubProjectName = DATA_PROPERTY(
    rdl=DEXPI_RDL.SUB_PROJECT_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the related sub-project.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='a sub-project')

DIAGRAM.MetaData.SubProjectNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.SUB_PROJECT_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the related sub-project.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='P3.1415-SP2')

DIAGRAM.MetaData.TotalNumberOfSheets = DATA_PROPERTY(
    rdl=DEXPI_RDL.TOTAL_NUMBER_OF_SHEETS,
    #TODO: total number with respect to what?
    description=r'''
        The total number of sheets.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=4)

DIAGRAM.MetaData.UnitIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.UNIT_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the related unit according to ISA-95.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='U-923-463')

DIAGRAM.MetaData.UnitName = DATA_PROPERTY(
    rdl=DEXPI_RDL.UNIT_ISA95_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the related unit according to ISA-95.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='a unit')


DIAGRAM.Symbol = CONCRETE_CLASS(
    superTypes=[DIAGRAM.RepresentationTypeGroup])

DIAGRAM.PipeFlowArrow = CONCRETE_CLASS(
    superTypes=[DIAGRAM.Symbol])

DIAGRAM.PipeSlopeSymbol = CONCRETE_CLASS(
    superTypes=[DIAGRAM.Symbol])

DIAGRAM.InsulationSymbol = CONCRETE_CLASS(
    superTypes=[DIAGRAM.Symbol])

DIAGRAM.CustomSymbol = CONCRETE_CLASS(
    superTypes=[DIAGRAM.Symbol])

DIAGRAM.Shape = CONCRETE_CLASS()

DIAGRAM.Shape.Name = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='ENTRIFUGAL_PUMP_SHAPE')

DIAGRAM.Shape.SymbolRegistrationNumber = DATA_PROPERTY(
    
    description='''
        A registration number that identifies the <OWNER>.
        
        The following format is recommended:
        
        :code:`[standard]:[version]-[id]-[transform]`
        
        where

        - :code:`standard` is the name of a drawing standard,
        
        - :code:`version` is the version the drawing standard, e.g., a year,
        
        - :code:`id` is the identifier used in the standard for the <OWNER>,
        
        - :code:`transform` gives the transformation of the <OWNER> w.r.t. its depiction in the
          standard.
          
          :code:`transform` is one of the following values:
          
          - :code:`A`: no transformation,
          
          - :code:`B`: rotation by 90°,
          
          - :code:`C`: rotation by 180°,
          
          - :code:`D`: rotation by 270°,
          
          - :code:`E`: mirrored,
          
          - :code:`F`: mirrored, rotation by 90°,
          
          - :code:`G`: mirrored, rotation by 180°,
          
          - :code:`H`: mirrored, rotation by 270°.''',
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='ISO10628:2012-2322-A')

DIAGRAM.Shape.Primitives = COMPOSITION_PROPERTY(
    description=r'''
        The primitives of the <OWNER>.
    ''',
    type=DIAGRAM.GraphicalPrimitive,
    lower=0,
    upper=None,
    isOrdered=True)

DIAGRAM.ShapeCatalogue = CONCRETE_CLASS()

DIAGRAM.ShapeCatalogue.Name = DATA_PROPERTY(
    description=r'''
        The name of the <OWNER>.
    ''',
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Shapes for example P&ID')

DIAGRAM.ShapeCatalogue.Shapes = COMPOSITION_PROPERTY(
    description=r'''
        The shapes of the <OWNER>.
    ''',
    type=DIAGRAM.Shape,
    lower=0,
    upper=None)

DIAGRAM.ShapeUsage = CONCRETE_CLASS(
    superTypes=[DIAGRAM.GraphicalElement])

DIAGRAM.ShapeUsage.IsMirrored = DATA_PROPERTY(
    type=BUILTIN.Boolean,
    lower=1,
    upper=1,
    exampleValue=False)

DIAGRAM.ShapeUsage.Position = DATA_PROPERTY(
    type=DIAGRAM.Point,
    lower=1,
    upper=1,
    exampleValue=DIAGRAM.Point(
        X=20.0, Y=20.0))

DIAGRAM.ShapeUsage.Rotation = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=0.0)

DIAGRAM.ShapeUsage.ScaleX = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=1.0)

DIAGRAM.ShapeUsage.ScaleY = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=1.0)

DIAGRAM.ShapeUsage.Shape = REFERENCE_PROPERTY(
    description=r'''
        The shape used by the <OWNER>.
    ''',
    type=DIAGRAM.Shape,
    lower=1,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)
    
#---------------
#   Enumerations
#---------------

DIAGRAM.ConfidentialityClassification = ENUMERATION()
DIAGRAM.ConfidentialityClassification.ConfidentialInformation = ENUMERATION_LITERAL(
    rdl_uri='http://data.posccaesar.org/rdl/RDS4316590816',
    rdl_label='CONFIDENTIAL INFORMATION',
    un_symbol='confidential')
DIAGRAM.ConfidentialityClassification.NonConfidentialInformation = ENUMERATION_LITERAL(
    rdl_uri='http://sandbox.dexpi.org/rdl/NonConfidentialInformation',
    rdl_label='NON CONFIDENTIAL INFORMATION',
    un_symbol='not confidential')
